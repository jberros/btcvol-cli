# Contributing to btcvol-cli

## Development Setup

```bash
git clone https://github.com/jberros/btcvol-cli.git
cd btcvol-cli
pip install -e .
```

## Making Changes

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## Testing

```bash
# Test the CLI
btcvol-submit test_model.py --name test

# Or run directly
python btcvol_submit.py test_model.py
```

## Code Style

- Follow PEP 8
- Add docstrings to functions
- Keep functions focused and testable

## Release Process

1. Update version in `setup.py` and `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create GitHub release
4. Build: `python -m build`
5. Upload: `twine upload dist/*`
