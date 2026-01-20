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

# Configuration
SUBMISSION_BASE = Path(__file__).parent / "deployment" / "model-orchestrator-local" / "data" / "submissions"
MODELS_CONFIG = Path(__file__).parent / "deployment" / "model-orchestrator-local" / "config" / "models.dev.yml"
BTCVOL_SOURCE = SUBMISSION_BASE / "model-1" / "btcvol"  # Reference btcvol module


def validate_model_file(model_path: Path) -> tuple[bool, str]:
    """Validate the model file exists and is the correct type."""
    if not model_path.exists():
        return False, f"Model file not found: {model_path}"
    
    if model_path.suffix not in ['.py', '.ipynb']:
        return False, f"Model file must be .py or .ipynb, got: {model_path.suffix}"
    
    # Check if file contains TrackerBase (basic check, will validate during extraction)
    content = model_path.read_text()
    if 'Tracker' not in content or 'predict' not in content:
        return False, "Model file must contain a Tracker class with predict() method"
    
    return True, "Valid"


def extract_model_code_from_notebook(notebook_path: Path) -> str:
    """Extract Python code from a Jupyter notebook."""
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
            
            # Skip cells with:
            # - Magic commands (%, !, etc.)
            # - Test code
            # - Installation commands
            # - Empty cells
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
    
    # Copy btcvol module
    if not BTCVOL_SOURCE.exists():
        raise FileNotFoundError(f"btcvol module not found at {BTCVOL_SOURCE}")
    
    print(f"📦 Copying btcvol module...")
    shutil.copytree(BTCVOL_SOURCE, submission_dir / "btcvol")
    
    # Create main.py
    if model_path.suffix == '.ipynb':
        print(f"📓 Extracting code from notebook...")
        code = extract_model_code_from_notebook(model_path)
    else:
        code = model_path.read_text()
    
    # Ensure proper import
    if 'from btcvol.tracker import TrackerBase' not in code:
        # Try to fix common import patterns
        code = code.replace('from btcvol import TrackerBase', 'from btcvol.tracker import TrackerBase')
    
    # Add required imports if missing
    required_imports = []
    if 'TrackerBase' in code and 'from btcvol.tracker import TrackerBase' not in code:
        required_imports.append('from btcvol.tracker import TrackerBase')
    if 'np.' in code and 'import numpy as np' not in code:
        required_imports.append('import numpy as np')
    
    if required_imports:
        code = '\n'.join(required_imports) + '\n\n\n' + code
    
    # Remove test execution code
    lines = code.split('\n')
    main_block_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith('if __name__'):
            main_block_start = i
            break
    
    if main_block_start is not None:
        code = '\n'.join(lines[:main_block_start])
    
    main_py = submission_dir / "main.py"
    main_py.write_text(code)
    print(f"✅ Created main.py")
    
    # Create requirements.txt
    requirements = submission_dir / "requirements.txt"
    
    # Check if model has any imports we should include
    import_patterns = {
        'numpy': 'numpy>=1.24.0',
        'pandas': 'pandas>=2.0.0',
        'scipy': 'scipy>=1.10.0',
        'sklearn': 'scikit-learn>=1.3.0',
    }
    
    deps = set()
    for pkg, req in import_patterns.items():
        if f'import {pkg}' in code:
            deps.add(req)
    
    if not deps:
        deps.add('numpy>=1.24.0')  # Default
    
    requirements.write_text('\n'.join(sorted(deps)) + '\n')
    print(f"✅ Created requirements.txt with: {', '.join(sorted(deps))}")
    
    return submission_dir


def update_models_config(submission_name: str, model_id: str) -> bool:
    """Update models.dev.yml with the new model."""
    try:
        with open(MODELS_CONFIG) as f:
            config = yaml.safe_load(f)
        
        # Check if model already exists
        existing_ids = [m['id'] for m in config.get('models', [])]
        if model_id in existing_ids:
            # Update existing model
            for model in config['models']:
                if model['id'] == model_id:
                    model['submission_id'] = submission_name
                    model['desired_state'] = 'RUNNING'
                    print(f"🔄 Updated existing model {model_id}")
                    break
        else:
            # Add new model
            new_model = {
                'id': model_id,
                'name': submission_name,
                'submission_id': submission_name,
                'crunch_id': 'btcvol',
                'desired_state': 'RUNNING',
                'cruncher_id': 'test_1'
            }
            
            if 'models' not in config:
                config['models'] = []
            
            config['models'].append(new_model)
            print(f"➕ Added new model {model_id}")
        
        # Write back
        with open(MODELS_CONFIG, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        return True
    except Exception as e:
        print(f"❌ Failed to update models config: {e}")
        return False


def trigger_deployment() -> bool:
    """Trigger the model deployment by restarting the orchestrator."""
    try:
        print(f"\n🚀 Deploying model...")
        result = subprocess.run(
            ['docker', 'restart', 'dvol-model-orchestrator-local'],
            capture_output=True,
            text=True,
            check=True
        )
        
        print(f"✅ Orchestrator restarted. Your model will be deployed shortly.")
        print(f"\n⏳ Waiting for deployment (this may take 30-60 seconds)...")
        time.sleep(5)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to restart orchestrator: {e}")
        return False


def check_deployment_status(model_id: str, max_wait: int = 60) -> str:
    """Check if the model was successfully deployed."""
    try:
        start_time = time.time()
        while time.time() - start_time < max_wait:
            result = subprocess.run(
                ['docker', 'logs', 'dvol-model-orchestrator-local', '--tail', '100'],
                capture_output=True,
                text=True
            )
            
            logs = result.stdout + result.stderr
            
            # Check for success
            if f"Model {model_id} is RUNNING" in logs:
                return "RUNNING"
            
            # Check for failure
            if f"Model {model_id}" in logs and "FAILED" in logs:
                return "FAILED"
            
            time.sleep(3)
        
        return "UNKNOWN"
    except Exception as e:
        print(f"⚠️  Could not check deployment status: {e}")
        return "UNKNOWN"


def main():
    parser = argparse.ArgumentParser(
        description='Submit a model to the BTC Volatility Competition',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python submit_model.py my_model.py
  python submit_model.py GARCH_Baseline.ipynb --name my-garch
  
Your model file should contain a class that inherits from TrackerBase
and implements the predict() method.
        """
    )
    
    parser.add_argument(
        'model_file',
        type=Path,
        help='Path to your model file (.py or .ipynb)'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        help='Custom name for your submission (auto-generated if not provided)'
    )
    
    parser.add_argument(
        '--no-deploy',
        action='store_true',
        help='Create submission structure but do not deploy (for testing)'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏆 BTC Volatility Competition - Model Submission Tool")
    print("=" * 60)
    
    # Validate model file
    print(f"\n📝 Validating model file: {args.model_file}")
    valid, message = validate_model_file(args.model_file)
    if not valid:
        print(f"❌ {message}")
        return 1
    print(f"✅ {message}")
    
    # Generate submission name and ID
    submission_name = generate_submission_name(args.name)
    model_id = generate_model_id()
    
    print(f"\n📋 Submission Details:")
    print(f"   Name: {submission_name}")
    print(f"   Model ID: {model_id}")
    
    try:
        # Create submission structure
        print(f"\n📁 Creating submission structure...")
        submission_dir = create_submission_structure(args.model_file, submission_name)
        print(f"✅ Submission created at: {submission_dir}")
        
        # Update configuration
        print(f"\n⚙️  Updating configuration...")
        if not update_models_config(submission_name, model_id):
            return 1
        print(f"✅ Configuration updated")
        
        if args.no_deploy:
            print(f"\n⏸️  Skipping deployment (--no-deploy flag)")
            print(f"\n✅ Submission ready! Run without --no-deploy to deploy.")
            return 0
        
        # Deploy
        if not trigger_deployment():
            return 1
        
        # Check status
        status = check_deployment_status(model_id)
        
        print("\n" + "=" * 60)
        if status == "RUNNING":
            print(f"✅ SUCCESS! Your model is now RUNNING")
            print(f"\n📊 View your model at: http://localhost:3000/models")
            print(f"   Model ID: {model_id}")
            print(f"   Submission: {submission_name}")
        elif status == "FAILED":
            print(f"❌ Deployment failed. Check logs with:")
            print(f"   docker logs dvol-model-orchestrator-local | grep {model_id}")
        else:
            print(f"⏳ Deployment status: {status}")
            print(f"   Check status with: docker logs dvol-model-orchestrator-local | grep {model_id}")
        print("=" * 60)
        
        return 0 if status == "RUNNING" else 1
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
