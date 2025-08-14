# Installation

This guide will help you install jinpy-utils and get your development environment ready.

## Requirements

Before installing jinpy-utils, ensure your system meets these requirements:

### Python Version

jinpy-utils requires **Python 3.12 or later**. Check your Python version:

```bash
python --version
# or
python3 --version
```

!!! info "Python Version Support"
    jinpy-utils follows the Python release cycle and supports the latest stable Python versions. Python 3.12+ is required for the latest type annotation features and performance improvements.

### Operating System

jinpy-utils is tested and supported on:

- **Linux** (Ubuntu 20.04+, CentOS 8+, Debian 10+)
- **macOS** (10.15+)
- **Windows** (10+, Windows Server 2019+)

## Installation Methods

### Using pip (Recommended)

Install jinpy-utils from PyPI using pip:

```bash
pip install jinpy-utils
```

### Using pip with extras

For development or specific use cases, install with extras:

=== "Development"

    ```bash
    pip install jinpy-utils[dev]
    ```

=== "Testing Only"

    ```bash
    pip install jinpy-utils[test]
    ```

=== "Documentation"

    ```bash
    pip install jinpy-utils[docs]
    ```

### Using uv (Fast Alternative)

If you're using [uv](https://github.com/astral-sh/uv), you can install jinpy-utils faster:

```bash
uv add jinpy-utils
```

Or for development:

```bash
uv add jinpy-utils[dev]
```

### Using Poetry

If you're using Poetry for dependency management:

```bash
poetry add jinpy-utils
```

Or for development dependencies:

```bash
poetry add --group dev jinpy-utils[dev]
```

### Using pipx (For CLI Tools)

If jinpy-utils includes CLI tools (future versions), install with pipx:

```bash
pipx install jinpy-utils
```

### From Source

For the latest development version or to contribute:

```bash
git clone https://github.com/jinto-ag/jinpy-utils.git
cd jinpy-utils
pip install -e .
```

Or with development dependencies:

```bash
pip install -e .[dev]
```

## Verify Installation

After installation, verify that jinpy-utils is properly installed:

```python title="verify_installation.py"
import jinpy_utils
from jinpy_utils.logger import get_logger
from jinpy_utils.base import JPYBaseException

# Check version
print(f"jinpy-utils version: {jinpy_utils.__version__}")

# Test basic functionality
logger = get_logger("test")
logger.info("jinpy-utils installed successfully!")

# Test exception handling
try:
    raise JPYBaseException(
        error_code="TEST_ERROR",
        message="This is a test error"
    )
except JPYBaseException as e:
    print(f"Exception handling works: {e.error_code}")
```

Run the verification script:

```bash
python verify_installation.py
```

Expected output:
```
jinpy-utils version: 0.1.0a0
2025-01-20 10:30:45.123 | INFO | test | jinpy-utils installed successfully!
Exception handling works: TEST_ERROR
```

## Development Setup

If you plan to contribute to jinpy-utils or need a development setup:

### 1. Clone the Repository

```bash
git clone https://github.com/jinto-ag/jinpy-utils.git
cd jinpy-utils
```

### 2. Set Up Virtual Environment

=== "Using venv"

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

=== "Using conda"

    ```bash
    conda create -n jinpy-utils python=3.12
    conda activate jinpy-utils
    ```

=== "Using uv"

    ```bash
    uv venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

### 3. Install Development Dependencies

```bash
pip install -e .[dev]
```

### 4. Install Pre-commit Hooks

```bash
pre-commit install
```

### 5. Run Tests

```bash
pytest
```

### 6. Verify Development Setup

```bash
# Run linting
ruff check src/

# Run type checking
mypy src/

# Run security checks
bandit -r src/

# Build documentation
mkdocs serve
```

## Troubleshooting

### Common Issues

#### Python Version Error

**Error**: `python: command not found` or wrong version

**Solution**: Install Python 3.12+ or update your PATH:

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install python3.12 python3.12-pip

# On macOS with Homebrew
brew install python@3.12

# On Windows
# Download from https://python.org or use winget
winget install Python.Python.3.12
```

#### Permission Errors

**Error**: `Permission denied` during installation

**Solution**: Use virtual environment or user installation:

```bash
# Virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install jinpy-utils

# User installation
pip install --user jinpy-utils
```

#### Import Errors

**Error**: `ModuleNotFoundError: No module named 'jinpy_utils'`

**Solutions**:

1. Ensure jinpy-utils is installed in the active environment:
   ```bash
   pip list | grep jinpy-utils
   ```

2. Check Python path:
   ```python
   import sys
   print(sys.path)
   ```

3. Reinstall in the correct environment:
   ```bash
   pip uninstall jinpy-utils
   pip install jinpy-utils
   ```

#### Version Conflicts

**Error**: Dependency conflicts during installation

**Solution**: Use fresh virtual environment:

```bash
python -m venv fresh_env
source fresh_env/bin/activate
pip install jinpy-utils
```

### Getting Help

If you encounter issues not covered here:

1. Search [existing issues](https://github.com/jinto-ag/jinpy-utils/issues)
2. Create a [new issue](https://github.com/jinto-ag/jinpy-utils/issues/new)
3. Join our [discussions](https://github.com/jinto-ag/jinpy-utils/discussions)

## Next Steps

Now that jinpy-utils is installed, continue with:

- [Quick Start Guide](quick-start.md) - Get started with basic usage
- [Configuration](configuration.md) - Learn about configuration options
- [Logger Guide](../guides/logger.md) - Deep dive into logging features

## Update and Uninstall

### Updating jinpy-utils

```bash
pip install --upgrade jinpy-utils
```

### Uninstalling jinpy-utils

```bash
pip uninstall jinpy-utils
```

To completely remove all traces:

```bash
pip uninstall jinpy-utils
# Remove cached files
python -c "import jinpy_utils; print(jinpy_utils.__file__)" 2>/dev/null || echo "Already removed"
```
