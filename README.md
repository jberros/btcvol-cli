# btcvol-cli - Model Submission Tool

Command-line tool for submitting models to the BTC Volatility Competition.

## Purpose

This CLI tool is for **submitting models to your local competition infrastructure**. It automates:
- Model validation
- Conversion of Jupyter notebooks to Python
- Creation of submission structure
- Deployment to the model orchestrator

## Installation

```bash
pip install git+https://github.com/jberros/btcvol-cli.git
```

## Usage

### Submit a Python file
```bash
btcvol-submit my_model.py --name my-volatility-model
```

### Submit a Jupyter notebook
```bash
btcvol-submit GARCH_Baseline.ipynb --name garch-model
```

## How It Works

1. **Validates** your model file (checks for TrackerBase inheritance)
2. **Converts** notebooks to Python (using crunch-convert)
3. **Creates** submission structure in `deployment/model-orchestrator-local/data/submissions/`
4. **Updates** `models.dev.yml` configuration
5. **Restarts** orchestrator to deploy your model

## Requirements

- Must be run from the competition infrastructure repository
- Model must inherit from `btcvol.TrackerBase`
- Model must implement `predict(asset, horizon, step)` method

## For Participants

Participants should NOT use this CLI directly. Instead:
- Use the web UI at http://localhost:3000/models
- Or submit via the competition platform

This CLI is for **local development and testing** of the competition infrastructure.

## Development

To contribute or modify:

```bash
git clone https://github.com/jberros/btcvol-cli.git
cd btcvol-cli
pip install -e .
```

## License

MIT License - See LICENSE file for details
