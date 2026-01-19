# btcvol-cli

Command-line tool for submitting models to CrunchDAO Bitcoin DVOL competitions.

[![PyPI version](https://badge.fury.io/py/btcvol-cli.svg)](https://badge.fury.io/py/btcvol-cli)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Installation

```bash
pip install btcvol-cli
```

Or install from GitHub:

```bash
pip install git+https://github.com/jberros/btcvol-cli.git
```

## Quick Start

Submit a Python model:

```bash
btcvol-submit my_model.py --name my-volatility-model
```

Submit a Jupyter notebook:

```bash
btcvol-submit GARCH_Baseline.ipynb --name garch-baseline
```

## Usage

### Basic Submission

```bash
btcvol-submit MODEL_FILE [OPTIONS]
```

**Arguments:**
- `MODEL_FILE` - Path to your model file (.py or .ipynb)

**Options:**
- `--name NAME` - Custom name for your model (auto-generated if not provided)
- `--submission-dir DIR` - Custom submission directory (default: auto-generated)

### Examples

**Submit Python file:**
```bash
btcvol-submit volatility_model.py
```

**Submit with custom name:**
```bash
btcvol-submit my_model.py --name advanced-garch-v2
```

**Submit Jupyter notebook:**
```bash
btcvol-submit GARCH_Baseline.ipynb --name my-garch-baseline
```

**Custom submission directory:**
```bash
btcvol-submit model.py --submission-dir /path/to/submissions/my-model
```

## Requirements

Your model must:
1. Inherit from `btcvol.TrackerBase`
2. Implement the `predict(asset, horizon, step)` method
3. Return a list of volatility predictions

Example model:

```python
from btcvol import TrackerBase

class MyVolatilityModel(TrackerBase):
    def predict(self, asset: str, horizon: int, step: int):
        num_predictions = horizon // step
        return [0.42] * num_predictions  # Your prediction logic here
```

## What It Does

The CLI tool:

1. ✅ **Validates** your model implements the required interface
2. ✅ **Extracts** code from Jupyter notebooks (skips magic commands)
3. ✅ **Bundles** the btcvol package with your submission
4. ✅ **Generates** requirements.txt automatically
5. ✅ **Updates** model configuration (models.dev.yml)
6. ✅ **Deploys** by restarting the orchestrator
7. ✅ **Monitors** build and deployment status

## Notebook Submission

When submitting Jupyter notebooks, the tool:
- Extracts only code cells (skips markdown)
- Removes Jupyter magic commands (`!pip install`, `%`, etc.)
- Skips test/validation cells
- Auto-adds missing imports (numpy, TrackerBase)
- Preserves your model logic exactly as written

## Deployment Environment

**Default Configuration:**
- Submission directory: `deployment/model-orchestrator-local/data/submissions/`
- Configuration file: `deployment/model-orchestrator-local/config/models.dev.yml`
- Network: `btcdvolnet`
- Orchestrator container: `dvol-model-orchestrator-local`

## Troubleshooting

**"Tracker class not found"**
- Ensure your class inherits from `TrackerBase`
- Check that you've implemented the `predict()` method

**"Module not found" errors**
- Add required packages to your model's dependencies
- The tool generates requirements.txt, but custom deps need manual addition

**"Build failed"**
- Check orchestrator logs: `docker logs dvol-model-orchestrator-local`
- Verify your model code has no syntax errors
- Ensure all imports are available

**Notebook conversion issues**
- Avoid Jupyter magic commands in production cells
- Test locally with `test_model_locally()` first
- Check that numpy imports are present

## Development

```bash
# Clone repository
git clone https://github.com/jberros/btcvol-cli.git
cd btcvol-cli

# Install in development mode
pip install -e .

# Run directly
python -m btcvol_cli.submit model.py
```

## Links

- **Main Package**: [btcvol](https://pypi.org/project/btcvol/) - Model development package
- **Competition**: [CrunchDAO](https://www.crunchdao.com/)
- **GitHub**: [btcvol-cli](https://github.com/jberros/btcvol-cli)
- **Issues**: [GitHub Issues](https://github.com/jberros/btcvol-cli/issues)

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

For CLI issues, [open an issue](https://github.com/jberros/btcvol-cli/issues) on GitHub.

For competition questions, visit the [CrunchDAO Discord](https://discord.gg/crunchdao).
