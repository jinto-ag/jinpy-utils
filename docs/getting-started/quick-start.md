# Quick Start

Get up and running with jinpy-utils in just a few minutes! This guide covers the essential features to get you started.

## Prerequisites

Make sure you have jinpy-utils installed. If not, see the [installation guide](installation.md).

```bash
pip install jinpy-utils
```

## Your First Logger

Let's start with the most commonly used feature - structured logging:

```python title="basic_logging.py"
from jinpy_utils.logger import get_logger

# Create a logger instance
logger = get_logger("my_app")

# Log some messages
logger.info("Application starting")
logger.info("Processing user request", user_id=123, action="login")
logger.warning("Low disk space", available_gb=2.1, threshold_gb=5.0)
logger.error("Database connection failed",
             error_code="DB_CONN_001",
             retry_count=3)
```

Output:
```json
{"timestamp": "2025-01-20T10:30:45.123Z", "level": "INFO", "logger": "my_app", "message": "Application starting"}
{"timestamp": "2025-01-20T10:30:45.124Z", "level": "INFO", "logger": "my_app", "message": "Processing user request", "user_id": 123, "action": "login"}
{"timestamp": "2025-01-20T10:30:45.125Z", "level": "WARNING", "logger": "my_app", "message": "Low disk space", "available_gb": 2.1, "threshold_gb": 5.0}
{"timestamp": "2025-01-20T10:30:45.126Z", "level": "ERROR", "logger": "my_app", "message": "Database connection failed", "error_code": "DB_CONN_001", "retry_count": 3}
```

## Structured Exception Handling

Handle errors consistently with structured exceptions:

```python title="exception_handling.py"
from jinpy_utils.base import JPYConfigurationError, JPYDatabaseError

def connect_to_database(config):
    """Example function that might fail."""
    if not config.get("database_url"):
        raise JPYConfigurationError(
            message="Database URL is required",
            config_key="database_url",
            suggestions=["Set DATABASE_URL environment variable",
                        "Add database_url to your configuration file"]
        )

    # Simulate database connection failure
    if config["database_url"] == "invalid":
        raise JPYDatabaseError(
            message="Failed to connect to database",
            database_url=config["database_url"],
            details={"error": "Connection timeout after 30s"},
            suggestions=["Check database server status",
                        "Verify connection parameters"]
        )

# Usage example
try:
    config = {"database_url": ""}  # Missing URL
    connect_to_database(config)
except JPYConfigurationError as e:
    print("Configuration Error:")
    print(f"  Message: {e.message}")
    print(f"  Key: {e.config_key}")
    print(f"  Suggestions: {e.suggestions}")

    # Convert to JSON for logging/API responses
    print(f"  JSON: {e.to_json()}")
```

Output:
```
Configuration Error:
  Message: Database URL is required
  Key: database_url
  Suggestions: ['Set DATABASE_URL environment variable', 'Add database_url to your configuration file']
  JSON: {"error_code": "CONFIGURATION_ERROR", "message": "Database URL is required", "config_key": "database_url", "suggestions": ["Set DATABASE_URL environment variable", "Add database_url to your configuration file"], "timestamp": "2025-01-20T10:30:45.127Z"}
```

## Async Logging

jinpy-utils supports async operations out of the box:

```python title="async_example.py"
import asyncio
from jinpy_utils.logger import get_logger

async def process_data(data_id: int):
    """Example async function with logging."""
    logger = get_logger("data_processor")

    logger.info("Starting data processing", data_id=data_id)

    try:
        # Simulate async work
        await asyncio.sleep(0.1)

        # Log progress
        logger.debug("Validating data", data_id=data_id, step="validation")
        await asyncio.sleep(0.1)

        logger.debug("Processing data", data_id=data_id, step="processing")
        await asyncio.sleep(0.1)

        logger.info("Data processing completed", data_id=data_id, status="success")
        return {"data_id": data_id, "status": "processed"}

    except Exception as e:
        logger.error("Data processing failed",
                    data_id=data_id,
                    error=str(e),
                    status="failed")
        raise

async def main():
    """Process multiple items concurrently."""
    tasks = [process_data(i) for i in range(1, 4)]
    results = await asyncio.gather(*tasks)

    logger = get_logger("main")
    logger.info("Batch processing completed",
               total_items=len(results),
               successful_items=len([r for r in results if r]))

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

Configure your logger for different environments:

```python title="configuration.py"
from jinpy_utils.logger import get_logger, create_development_config, create_production_config, set_global_config

# Set global development configuration
set_global_config(create_development_config())
dev_logger = get_logger("dev_app")
dev_logger.debug("This will be visible in development")

# Set global production configuration
set_global_config(create_production_config())
prod_logger = get_logger("prod_app")
prod_logger.debug("This won't be visible in production (INFO+ only)")
prod_logger.info("This will be logged in production")

# Custom configuration (per-logger)
from jinpy_utils.logger import LoggerConfig, ConsoleBackendConfig, LogLevel, LogFormat

custom_config = LoggerConfig(
    level=LogLevel.WARNING,  # Only WARNING and ERROR
    backends=[
        ConsoleBackendConfig(
            level=LogLevel.WARNING,
            format=LogFormat.STRUCTURED
        )
    ]
)

custom_logger = get_logger("custom_app", custom_config)
custom_logger.info("This won't be shown")  # Below WARNING level
custom_logger.warning("This will be shown")  # WARNING level
```

## File Logging

Log to files with automatic rotation:

```python title="file_logging.py"
from jinpy_utils.logger import (
    get_logger,
    LoggerConfig,
    FileBackendConfig,
    LogLevel
)

# Configure file logging
file_config = LoggerConfig(
    level=LogLevel.DEBUG,
    backends=[
        FileBackendConfig(
            level=LogLevel.INFO,
            file_path="logs/app.log",
            max_size_mb=10,  # Rotate after 10MB
            backup_count=5,  # Keep 5 old files
            encoding="utf-8"
        )
    ]
)

logger = get_logger("file_app", file_config)

# These will be written to the file
logger.info("Application started", version="1.0.0")
logger.warning("High memory usage", usage_percent=85)
logger.error("API call failed", endpoint="/api/users", status_code=500)
```

## Exception Registry

Register custom exception types for consistent error handling:

```python title="custom_exceptions.py"
from jinpy_utils.base import JPYBaseException, register_exception, create_exception

# Define a custom exception
class JPYPaymentError(JPYBaseException):
    """Exception for payment-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            error_code="PAYMENT_ERROR",
            message=message,
            **kwargs
        )

# Register the exception
register_exception("PAYMENT_ERROR", JPYPaymentError)

# Now you can create instances by error code
def process_payment(amount: float, card_number: str):
    """Example payment processing function."""
    if amount <= 0:
        # Create exception using the registry
        raise create_exception(
            "PAYMENT_ERROR",
            message="Invalid payment amount",
            amount=amount,
            suggestions=["Ensure amount is greater than 0"]
        )

    # Simulate card validation
    if not card_number or len(card_number) < 13:
        raise JPYPaymentError(
            message="Invalid card number",
            card_number="****" + card_number[-4:] if len(card_number) >= 4 else "****",
            suggestions=["Verify card number format",
                        "Check for typos in card number"]
        )

# Usage
try:
    process_payment(-10.0, "")
except JPYPaymentError as e:
    print(f"Payment failed: {e.message}")
    print(f"Suggestions: {', '.join(e.suggestions)}")
```

## Complete Example Application

Here's a complete example that puts it all together:

```python title="complete_example.py"
import asyncio
from typing import List, Dict, Any
from jinpy_utils.logger import get_logger, create_development_config
from jinpy_utils.base import JPYValidationError, JPYDatabaseError

class UserService:
    """Example service class using jinpy-utils."""

    def __init__(self):
        self.logger = get_logger("user_service", create_development_config())
        self.users_db: List[Dict[str, Any]] = []

    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user with validation and logging."""
        self.logger.info("Creating new user", user_data=user_data)

        try:
            # Validate user data
            self._validate_user_data(user_data)

            # Simulate async database operation
            user = await self._save_to_database(user_data)

            self.logger.info("User created successfully",
                           user_id=user["id"],
                           username=user["username"])

            return user

        except (JPYValidationError, JPYDatabaseError) as e:
            self.logger.error("User creation failed",
                            error=e.to_dict(),
                            user_data=user_data)
            raise
        except Exception as e:
            self.logger.error("Unexpected error during user creation",
                            error=str(e),
                            user_data=user_data)
            raise

    def _validate_user_data(self, user_data: Dict[str, Any]) -> None:
        """Validate user data."""
        if not user_data.get("username"):
            raise JPYValidationError(
                message="Username is required",
                field="username",
                value=user_data.get("username"),
                suggestions=["Provide a valid username"]
            )

        if not user_data.get("email"):
            raise JPYValidationError(
                message="Email is required",
                field="email",
                value=user_data.get("email"),
                suggestions=["Provide a valid email address"]
            )

    async def _save_to_database(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate saving to database."""
        # Simulate network delay
        await asyncio.sleep(0.1)

        # Check if username already exists
        if any(u["username"] == user_data["username"] for u in self.users_db):
            raise JPYDatabaseError(
                message="Username already exists",
                table="users",
                operation="insert",
                details={"username": user_data["username"]},
                suggestions=["Choose a different username"]
            )

        # Create user
        user = {
            "id": len(self.users_db) + 1,
            "username": user_data["username"],
            "email": user_data["email"],
            "created_at": "2025-01-20T10:30:45.127Z"
        }

        self.users_db.append(user)
        return user

async def main():
    """Main application function."""
    logger = get_logger("main", create_development_config())
    service = UserService()

    logger.info("Application starting")

    # Test data
    test_users = [
        {"username": "alice", "email": "alice@example.com"},
        {"username": "bob", "email": "bob@example.com"},
        {"username": "", "email": "invalid@example.com"},  # Invalid
        {"username": "alice", "email": "alice2@example.com"},  # Duplicate
    ]

    for user_data in test_users:
        try:
            user = await service.create_user(user_data)
            logger.info("User created", user_id=user["id"])
        except Exception as e:
            logger.warning("Skipping invalid user",
                          user_data=user_data,
                          reason=str(e))

    logger.info("Application completed",
               total_users=len(service.users_db))

if __name__ == "__main__":
    asyncio.run(main())
```

## Next Steps

Now that you've got the basics down, explore more advanced features:

### Deep Dive Guides
- [Logger Guide](../guides/logger.md) - Complete logging guide
- [Base Exceptions API](../reference/base/exceptions.md) - Exception handling reference

### Configuration
- [Configuration Guide](configuration.md) - Environment-specific setups

### API Reference
- [Logger API](../reference/logger/core.md) - Complete logger documentation
- [Exceptions API](../reference/base/exceptions.md) - Exception classes and methods
- [Time Utils API](../reference/utils/time.md) - Time utility functions

### Development
- [Contributing Guidelines](https://github.com/jinto-ag/jinpy-utils/blob/main/CONTRIBUTING.md) - Help improve jinpy-utils

## Common Patterns

Here are some common patterns you might find useful:

### Structured Logging with Context

```python
from contextlib import contextmanager
from jinpy_utils.logger import get_logger

@contextmanager
def log_operation(operation_name: str, **context):
    logger = get_logger("operations")
    logger.info(f"Starting {operation_name}", operation=operation_name, **context)
    try:
        yield
        logger.info(f"Completed {operation_name}", operation=operation_name, **context, status="success")
    except Exception as e:
        logger.error(f"Failed {operation_name}", operation=operation_name, **context, status="failed", error=str(e))
        raise

# Usage
with log_operation("user_registration", user_id=123):
    # Your operation here
    pass
```

### Exception Chain

```python
from jinpy_utils.base import JPYDatabaseError, JPYValidationError

try:
    # Some operation
    pass
except ValidationError as e:
    raise JPYValidationError(
        message="Data validation failed",
        original_error=str(e)
    ) from e
except ConnectionError as e:
    raise JPYDatabaseError(
        message="Database connection failed",
        original_error=str(e)
    ) from e
```

## Getting Help

If you need help:

- Browse the [API reference](../reference/index.md)
- Ask questions in [GitHub Discussions](https://github.com/jinto-ag/jinpy-utils/discussions)
- Report issues on [GitHub Issues](https://github.com/jinto-ag/jinpy-utils/issues)
