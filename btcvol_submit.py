#!/usr/bin/env python3
"""
BTC Volatility Competition - Model Submission CLI Tool

This tool allows you to submit your volatility prediction model to the competition.
It handles the creation of the submission structure and triggers the model deployment.

Usage:
    python submit_model.py <model_file> [--name <model_name>]
    
Examples:
    python submit_model.py my_model.py
    python submit_model.py GARCH_Baseline.ipynb --name my-garch-model
"""

import argparse
import os
import sys
import shutil
import yaml
import subprocess
from pathlib import Path
import hashlib
import time
import re
import ast
import inspect

# Configuration
SUBMISSION_BASE = Path(__file__).parent / "deployment" / "model-orchestrator-local" / "data" / "submissions"
MODELS_CONFIG = Path(__file__).parent / "deployment" / "model-orchestrator-local" / "config" / "models.dev.yml"


def validate_python_file(file_path: Path) -> tuple[bool, str]:
    """Validate a Python file for TrackerBase implementation."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        # Look for class that inherits from TrackerBase
        tracker_found = False
        predict_found = False
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check if class inherits from TrackerBase
                for base in node.bases:
                    if isinstance(base, ast.Name) and 'Tracker' in base.id:
                        tracker_found = True
                        
                        # Check if predict method is implemented
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name == 'predict':
                                predict_found = True
                                break
        
        if not tracker_found:
            return False, "No class inheriting from TrackerBase found"
        if not predict_found:
            return False, "Tracker class must implement predict() method"
            
        return True, "Valid"
        
    except SyntaxError as e:
        return False, f"Syntax error in Python file: {e}"
    except Exception as e:
        return False, f"Error validating file: {e}"


def validate_model_file(model_path: Path) -> tuple[bool, str]:
    """Validate the model file exists and is the correct type."""
    if not model_path.exists():
        return False, f"Model file not found: {model_path}"
    
    if model_path.suffix not in ['.py', '.ipynb']:
        return False, f"Model file must be .py or .ipynb, got: {model_path.suffix}"
    
    # For Python files, do AST-based validation
    if model_path.suffix == '.py':
        return validate_python_file(model_path)
    
    # For notebooks, we'll validate after conversion
    return True, "Valid notebook (will validate after conversion)"


def extract_model_code_from_notebook(notebook_path: Path) -> str:
    """Extract Python code from a Jupyter notebook using crunch-convert."""
    try:
        from crunch_convert import convert_notebook
        
        # Convert notebook to Python using crunch-convert
        python_code = convert_notebook(str(notebook_path))
        
        # Validate the converted code
        try:
            ast.parse(python_code)
        except SyntaxError as e:
            raise ValueError(f"Converted code has syntax errors: {e}")
        
        return python_code
        
    except ImportError:
        # Fallback to basic JSON parsing if crunch-convert not available
        print("⚠️  Warning: crunch-convert not installed, using basic notebook parser")
        print("   Install with: pip install crunch-convert")
        import json
        
        with open(notebook_path) as f:
            notebook = json.load(f)
        
        code_cells = []
        for cell in notebook.get('cells', []):
            if cell.get('cell_type') == 'code':
                source = cell.get('source', [])
                if isinstance(source, list):
                    code = ''.join(source)
                else:
                    code = source
                
                # Skip cells with magic commands, test code, installations
                stripped = code.strip()
                if (not stripped or 
                    stripped.startswith('%') or 
                    stripped.startswith('!') or
                    'test_model_locally' in code or
                    'pip install' in code or
                    '# Test' in code):
                    continue
                
                code_cells.append(code)
        
        return '\n\n'.join(code_cells)


def generate_submission_name(model_name: str = None) -> str:
    """Generate a unique submission name."""
    if model_name:
        # Sanitize user-provided name
        name = re.sub(r'[^a-z0-9-]', '-', model_name.lower())
        name = re.sub(r'-+', '-', name).strip('-')
    else:
        # Generate from timestamp
        name = f"submission-{int(time.time())}"
    
    return name


def generate_model_id() -> str:
    """Generate a unique model ID."""
    # Use timestamp-based ID to avoid conflicts
    base_id = 12315  # Start after existing models
    timestamp = int(time.time()) % 10000  # Last 4 digits of timestamp
    return str(base_id + timestamp)


def create_submission_structure(model_path: Path, submission_name: str) -> Path:
    """Create the submission directory structure."""
    submission_dir = SUBMISSION_BASE / submission_name
    
    if submission_dir.exists():
        print(f"⚠️  Submission '{submission_name}' already exists. Overwriting...")
        shutil.rmtree(submission_dir)
    
    submission_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📦 Creating submission structure in {submission_dir}...")
    
    # Extract model code
    if model_path.suffix == '.ipynb':
        print(f"📓 Converting notebook to Python...")
        model_code = extract_model_code_from_notebook(model_path)
    else:
        model_code = model_path.read_text()
    
    # Create main.py
    main_py = submission_dir / "main.py"
    main_py.write_text(model_code)
    print(f"✅ Created main.py")
    
    # Validate the generated Python file
    valid, msg = validate_python_file(main_py)
    if not valid:
        shutil.rmtree(submission_dir)
        raise ValueError(f"Generated model code is invalid: {msg}")
    
    # Create requirements.txt
    requirements = submission_dir / "requirements.txt"
    requirements.write_text("btcvol>=1.0.0\n")
    print(f"✅ Created requirements.txt")
    
    return submission_dir


def register_submission(submission_name: str, model_id: str):
    """Register the submission in models.dev.yml."""
    if not MODELS_CONFIG.exists():
        raise FileNotFoundError(f"Models config not found: {MODELS_CONFIG}")
    
    # Load existing config
    with open(MODELS_CONFIG) as f:
        config = yaml.safe_load(f) or {}
    
    if 'models' not in config:
        config['models'] = []
    
    # Check if model already exists
    existing = [m for m in config['models'] if m.get('name') == submission_name]
    if existing:
        print(f"⚠️  Model '{submission_name}' already registered. Updating...")
        config['models'] = [m for m in config['models'] if m.get('name') != submission_name]
    
    # Add new model
    new_model = {
        'id': model_id,
        'name': submission_name,
        'submissionPath': f"/data/submissions/{submission_name}"
    }
    config['models'].append(new_model)
    
    # Write config
    with open(MODELS_CONFIG, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"✅ Registered model in {MODELS_CONFIG}")
    print(f"   Model ID: {model_id}")


def trigger_deployment():
    """Trigger the model deployment by restarting the orchestrator."""
    print("\n🚀 Triggering model deployment...")
    print("   Note: This will restart the model orchestrator")
    
    try:
        # Restart orchestrator container
        result = subprocess.run(
            ["docker", "compose", "restart", "model-orchestrator"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ Orchestrator restarted successfully")
            print("\n📊 Check the models menu in the UI to see your submission")
        else:
            print(f"⚠️  Warning: Failed to restart orchestrator: {result.stderr}")
            print("   Please manually restart: docker compose restart model-orchestrator")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not restart orchestrator: {e}")
        print("   Please manually restart: docker compose restart model-orchestrator")


def main():
    parser = argparse.ArgumentParser(
        description="Submit a volatility prediction model to the competition"
    )
    parser.add_argument(
        'model_file',
        type=Path,
        help="Path to model file (.py or .ipynb)"
    )
    parser.add_argument(
        '--name',
        type=str,
        help="Custom submission name (optional, generated if not provided)"
    )
    
    args = parser.parse_args()
    
    # Validate model file
    print(f"🔍 Validating {args.model_file}...")
    valid, msg = validate_model_file(args.model_file)
    if not valid:
        print(f"❌ Validation failed: {msg}")
        sys.exit(1)
    print(f"✅ {msg}")
    
    # Generate submission name and ID
    submission_name = generate_submission_name(args.name)
    model_id = generate_model_id()
    
    print(f"\n📝 Submission details:")
    print(f"   Name: {submission_name}")
    print(f"   Model ID: {model_id}")
    
    try:
        # Create submission
        submission_dir = create_submission_structure(args.model_file, submission_name)
        
        # Register in config
        register_submission(submission_name, model_id)
        
        # Trigger deployment
        trigger_deployment()
        
        print(f"\n✅ Submission complete!")
        print(f"   Submission directory: {submission_dir}")
        
    except Exception as e:
        print(f"\n❌ Submission failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
