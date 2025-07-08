# CI/CD Setup for PyLogMerge

This document describes the Continuous Integration and Continuous Deployment setup for the PyLogMerge project.

## GitHub Actions Workflows

### 1. Build and Test (`build.yml`)

**Triggers:**
- Push to main/master/develop branches
- Pull requests to main/master/develop branches

**What it does:**
- Tests on Python 3.10, 3.11, 3.12
- Tests on Ubuntu, Windows, and macOS
- Installs system dependencies (X11 libraries for PyQt5 on Linux)
- Runs code quality checks:
  - `ruff` for linting
  - `black` for code formatting
  - `mypy` for type checking
  - `pytest` for unit tests
- Builds the Python package using `python -m build`
- Uploads build artifacts for each OS/Python combination

**Special considerations:**
- Uses `xvfb` on Linux for headless PyQt5 testing
- Sets `QT_QPA_PLATFORM=offscreen` for GUI testing
- Caches pip packages for faster builds
- MyPy errors are non-blocking due to potential PyQt5 compatibility issues

### 2. Release (`release.yml`)

**Triggers:**
- Push of version tags (format: `v*.*.*`, e.g., `v1.0.0`)

**What it does:**
- Builds the package
- Creates a GitHub release with auto-generated release notes
- Uploads built packages to the GitHub release
- Publishes to PyPI (requires `PYPI_API_TOKEN` secret)

### 3. Dependabot (`dependabot.yml`)

**What it does:**
- Weekly dependency updates for Python packages
- Weekly updates for GitHub Actions
- Automatically creates PRs for dependency updates
- Assigns PRs to the repository owner

## Package Configuration

### `pyproject.toml`

The project uses modern Python packaging with:
- **Build system:** `setuptools` with `build` backend
- **Python requirement:** 3.10+
- **Dependencies:** PyQt5
- **Dev dependencies:** pytest, black, ruff, mypy
- **Entry point:** `logmerge` command

### Tool configurations included:
- **pytest:** Test discovery and execution settings
- **ruff:** Fast Python linter with comprehensive rule set
- **black:** Code formatting with 88-character line length
- **mypy:** Type checking with strict settings and PyQt5 import ignoring

## Local Development

### Setting up the development environment:

```bash
# Clone the repository
git clone <repository-url>
cd pylogmerge

# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check src/

# Format code
black src/

# Type checking
mypy src/logmerge/
```

### Building the package locally:

```bash
# Install build dependencies
pip install build

# Build the package
python -m build

# The built package will be in dist/
```

## Release Process

1. **Update version** in `src/logmerge/__init__.py`
2. **Commit and push** changes
3. **Create and push a tag:**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. The release workflow will automatically:
   - Build the package
   - Create a GitHub release
   - Publish to PyPI (if token is configured)

## Required Secrets

To enable PyPI publishing, add these secrets to your GitHub repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add `PYPI_API_TOKEN` with your PyPI API token

To get a PyPI API token:
1. Create an account on [PyPI](https://pypi.org/)
2. Go to Account Settings → API tokens
3. Create a new token for this project

## Status Badges

Add these badges to your README.md:

```markdown
[![Build Status](https://github.com/faisal-shah/pylogmerge/workflows/Build%20and%20Test/badge.svg)](https://github.com/faisal-shah/pylogmerge/actions)
[![PyPI version](https://badge.fury.io/py/logmerge.svg)](https://badge.fury.io/py/logmerge)
[![Python versions](https://img.shields.io/pypi/pyversions/logmerge.svg)](https://pypi.org/project/logmerge/)
```

## Troubleshooting

### Common CI Issues:

1. **PyQt5 import errors on CI:**
   - The workflow installs necessary system dependencies
   - Uses virtual display (xvfb) on Linux
   - Sets headless mode with `QT_QPA_PLATFORM=offscreen`

2. **Test failures:**
   - Check if tests require GUI components
   - Ensure tests don't depend on specific file paths
   - Mock external dependencies

3. **Build failures:**
   - Verify `pyproject.toml` syntax
   - Check that all dependencies are properly specified
   - Ensure version string in `__init__.py` is valid

4. **MyPy errors:**
   - Currently set to continue on error due to PyQt5 compatibility
   - Add type stubs or ignore patterns as needed

5. **Deprecated action warnings:**
   - The workflows use the latest action versions (as of July 2025):
     - `actions/checkout@v4`
     - `actions/setup-python@v5`
     - `actions/cache@v4`
     - `actions/upload-artifact@v4`
     - `softprops/action-gh-release@v2`
   - If you see deprecation warnings, check for newer versions

### Recent Updates:

- **July 2025:** Updated all GitHub Actions to latest versions to fix deprecation warnings
- Actions updated: setup-python (v4→v5), cache (v3→v4), upload-artifact (v3→v4), gh-release (v1→v2)

For more help, check the GitHub Actions logs or open an issue.
