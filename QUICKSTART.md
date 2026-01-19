# btcvol-cli Quick Start

## Installation

```bash
pip install btcvol-cli
```

## Commands

### Submit a model

```bash
btcvol-submit MODEL_FILE [--name NAME] [--submission-dir DIR]
```

### Examples

```bash
# Basic submission
btcvol-submit my_model.py

# With custom name
btcvol-submit volatility_model.py --name advanced-garch-v2

# Submit notebook
btcvol-submit GARCH_Baseline.ipynb --name garch-baseline
```

## What You Need

A Python class that inherits from `btcvol.TrackerBase`:

```python
from btcvol import TrackerBase

class MyModel(TrackerBase):
    def predict(self, asset: str, horizon: int, step: int):
        num_predictions = horizon // step
        return [0.42] * num_predictions
```

## Testing First

```bash
pip install btcvol
python -c "from btcvol import test_model_locally; from your_model import YourModel; test_model_locally(YourModel)"
```

## Troubleshooting

**Import errors:** Make sure `btcvol` is installed: `pip install btcvol`

**"Tracker not found":** Check your class inherits from `TrackerBase` and has `predict()` method

**Build failures:** Check `docker logs dvol-model-orchestrator-local`
