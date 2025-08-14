# API Reference

Complete API documentation for jinpy-utils, automatically generated from source code.

## Overview

This reference covers all public APIs, classes, functions, and modules in jinpy-utils. The documentation is generated directly from the source code, ensuring it's always up-to-date.

## Package Structure

::: jinpy_utils
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: false
      members:
        - __version__
        - __author__
        - __email__

## Core Modules

### Logger Module

High-performance structured logging with async support.

- **[Core Classes](logger/core.md)** - Main logger classes and factory functions
- **[Backends](logger/backends.md)** - Output backends (Console, File, REST API, WebSocket)
- **[Configuration](logger/config.md)** - Configuration classes and presets
- **[Exceptions](logger/exceptions.md)** - Logger-specific exception classes

**Quick Start:**
```python
from jinpy_utils.logger import get_logger
logger = get_logger("my_app")
logger.info("Hello, world!")
```

### Base Module

Structured exceptions and registry helpers.

- **[Exceptions](base/exceptions.md)** - Base and derived exception classes
- **[Registry](base/registry.md)** - Exception registry and factory functions
- **[Models](base/models.md)** - Data models and schemas

**Quick Start:**
```python
from jinpy_utils.base import JPYConfigurationError
raise JPYConfigurationError(message="Invalid config", config_key="API_KEY")
```

### Utils Module

Cross-cutting helpers and common patterns.

- **[Time Utilities](utils/time.md)** - Time-related helper functions

**Quick Start:**
```python
from jinpy_utils.utils import get_current_datetime
timestamp = get_current_datetime()
```

## Navigation Tips

- **Search**: Use the search box to quickly find classes, functions, or concepts
- **Cross-references**: Click on type annotations and function names to navigate between related items
- **Source code**: Click on source links to view the actual implementation
- **Examples**: Most functions include usage examples in their docstrings

## API Stability

jinpy-utils follows semantic versioning:

- **Major version** (X.0.0): Breaking API changes
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

### Stability Levels

| Level | Description | Guarantee |
|-------|-------------|-----------|
| **Stable** | Public API | Backward compatible within major version |
| **Experimental** | New features | May change in minor versions |
| **Internal** | Implementation details | No compatibility guarantee |

All documented APIs are considered **Stable** unless marked otherwise.

## Type Annotations

All public APIs include comprehensive type annotations. For best experience:

1. Use a type checker like mypy
2. Enable type checking in your IDE
3. Use `from __future__ import annotations` for forward references

Example:
```python
from __future__ import annotations
from typing import Optional
from jinpy_utils.logger import Logger

def setup_logger(name: str, level: Optional[str] = None) -> Logger:
    return get_logger(name)
```

## Error Handling

All jinpy-utils APIs use structured exceptions. Common patterns:

```python
from jinpy_utils.base import JPYBaseException

try:
    # jinpy-utils operation
    pass
except JPYBaseException as e:
    # Handle structured error
    print(f"Error: {e.error_code}")
    print(f"Message: {e.message}")
    print(f"Suggestions: {e.suggestions}")
except Exception as e:
    # Handle unexpected error
    print(f"Unexpected error: {e}")
```

## Performance Notes

jinpy-utils is optimized for production use:

- **Async support**: All I/O operations support async/await
- **Lazy loading**: Modules are imported only when needed
- **Efficient serialization**: JSON serialization is optimized
- **Memory management**: Automatic cleanup of resources

For performance-critical applications, consider:

1. Using async versions of functions where available
2. Batching operations when possible
3. Configuring appropriate buffer sizes
4. Using production-optimized configurations

## Contributing to Documentation

The API documentation is generated from docstrings in the source code. To improve it:

1. Follow Google docstring format
2. Include type hints for all parameters and return values
3. Provide usage examples for public functions
4. Add `Raises:` sections for exceptions
5. Include performance notes where relevant

Example docstring:
```python
def example_function(name: str, count: int = 1) -> list[str]:
    """Generate example strings.

    Args:
        name: The base name for generated strings.
        count: Number of strings to generate. Defaults to 1.

    Returns:
        List of generated strings.

    Raises:
        ValueError: If count is negative.

    Example:
        >>> example_function("test", 2)
        ["test_0", "test_1"]

    Note:
        This function is optimized for small count values.
    """
```

## External Resources

- **Source Code**: [GitHub Repository](https://github.com/jinto-ag/jinpy-utils)
- **Issue Tracker**: [GitHub Issues](https://github.com/jinto-ag/jinpy-utils/issues)
- **PyPI Package**: [jinpy-utils on PyPI](https://pypi.org/project/jinpy-utils/)
- **Type Stubs**: Included in package (py.typed)
