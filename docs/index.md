# jinpy-utils

## Quick Navigation

!!! info "Getting Started"
    Get up and running with jinpy-utils in minutes with our comprehensive installation and setup guide.

    **[→ Get Started](getting-started/installation.md)**

!!! example "User Guide"
    Learn how to use jinpy-utils effectively with detailed guides covering all major features and use cases.

    **[→ Learn More](guides/logger.md)**

!!! note "API Reference"
    Complete API documentation with examples, generated directly from the source code.

    **[→ Browse API](reference/index.md)**

!!! tip "Open Source"
    jinpy-utils is open source and welcomes contributions from the community.

    **[→ Contribute](https://github.com/jinto-ag/jinpy-utils/blob/main/CONTRIBUTING.md)**

## Overview

**jinpy-utils** is a collection of minimal, type-safe Python utilities designed for modern Python development. It follows industry best practices including PEP 8 compliance, comprehensive type hints, and maintains high test coverage.

### Key Features

- **:material-format-list-bulleted-type: Type Safety**: Full type annotations and mypy compatibility
- **:material-speedometer: High Performance**: Optimized for production workloads
- **:material-puzzle: Modular Design**: Use only what you need
- **:material-test-tube: Well Tested**: Comprehensive test coverage (>80%)
- **:material-book-open: Well Documented**: Clear documentation with examples

### Core Packages

=== ":material-math-log: Logger"

    High-performance structured logging with async support and multiple backends.

    ```python
    from jinpy_utils.logger import get_logger

    logger = get_logger("my_app")
    logger.info("Application started", user_id=123, version="1.0.0")
    ```

    **Features:**
    - Multiple backends (Console, File, REST API, WebSocket)
    - Async/await support
    - Structured JSON logging
    - Performance optimized
    - Cloud-ready configurations

=== ":material-alert: Base Exceptions"

    Structured exceptions with consistent payload for reliable error handling.

    ```python
    from jinpy_utils.base import JPYConfigurationError

    raise JPYConfigurationError(
        message="Missing configuration",
        config_key="API_KEY",
        suggestions=["Set API_KEY in environment variables"]
    )
    ```

    **Features:**
    - Structured error details
    - JSON serialization
    - Exception registry
    - Consistent error format
    - Built-in remediation guidance

=== ":material-tools: Utilities"

    Cross-cutting helpers and common patterns for Python applications.

    ```python
    from jinpy_utils.utils import current_timestamp, format_duration

    start_time = current_timestamp()
    # ... do work ...
    duration = format_duration(current_timestamp() - start_time)
    ```

    **Features:**
    - Time utilities
    - Common patterns
    - Helper functions
    - Type-safe implementations

## Requirements

- **Python**: 3.12+
- **Type Checking**: mypy compatible
- **Code Style**: PEP 8 compliant with Ruff
- **Testing**: pytest with async support

## Installation

Install jinpy-utils using pip:

```bash
pip install jinpy-utils
```

Or with specific extras for development:

```bash
pip install jinpy-utils[dev]
```

## Quick Example

Here's a complete example showing the key features:

```python title="example.py"
import asyncio
from jinpy_utils.logger import get_logger, create_development_config, set_global_config
from jinpy_utils.base import JPYBaseException

# Configure logging globally
set_global_config(create_development_config())
logger = get_logger("example")

async def main():
    try:
        logger.info("Starting application", version="1.0.0")

        # Your application logic here
        await process_data()

        logger.info("Application completed successfully")

    except JPYBaseException as e:
        logger.error("Application failed", error=e.to_dict())
    except Exception as e:
        logger.error("Unexpected error", error=str(e))

async def process_data():
    # Simulate some async work
    await asyncio.sleep(0.1)
    logger.debug("Processing data", step="validation")

if __name__ == "__main__":
    asyncio.run(main())
```

## What's Next?

!!! question "New to jinpy-utils?"
    Start with our [installation guide](getting-started/installation.md) and [quick start tutorial](getting-started/quick-start.md).

!!! success "Ready to dive deeper?"
    Explore our comprehensive [user guides](guides/logger.md) for detailed explanations and examples.

!!! info "Need API details?"
    Check out the [API reference](reference/index.md) for complete documentation of all classes and functions.

!!! heart "Want to contribute?"
    Read our [contributing guidelines](https://github.com/jinto-ag/jinpy-utils/blob/main/CONTRIBUTING.md) to get started with development.

## Community and Support

- **Issues**: Report bugs and request features on [GitHub Issues](https://github.com/jinto-ag/jinpy-utils/issues)
- **Discussions**: Ask questions and share ideas on [GitHub Discussions](https://github.com/jinto-ag/jinpy-utils/discussions)
- **Email**: Contact the maintainer at [project.jintoag@gmail.com](mailto:project.jintoag@gmail.com)

## License

jinpy-utils is released under the [MIT License](https://github.com/jinto-ag/jinpy-utils/blob/main/LICENSE).
