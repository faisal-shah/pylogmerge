# Tests

This directory contains the test suite for the logmerge package.

## Structure

- `conftest.py` - Test configuration and shared fixtures
- `test_basic.py` - Basic package import and functionality tests
- Additional test files can be added as needed

## Running Tests

To run the tests locally:

```bash
# Install test dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=logmerge

# Run specific test file
pytest tests/test_basic.py
```

## CI Testing

The tests are automatically run in GitHub Actions CI on:
- Python 3.10, 3.11, 3.12
- Ubuntu, Windows, and macOS
- For all pushes and pull requests to main branches

Note: GUI tests require special handling in CI environments with virtual displays.
