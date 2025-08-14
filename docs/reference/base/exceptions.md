# Base Exceptions API

Core exception classes and structured error handling.

## Base Exception Class

### JPYBaseException

::: jinpy_utils.base.JPYBaseException
    options:
      show_root_heading: true
      show_root_toc_entry: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table
      members:
        - __init__
        - __new__
        - __str__
        - __repr__
        - __eq__
        - __hash__
        - __reduce__
        - __setstate__
        - __getstate__
        - to_dict
        - to_json
        - from_dict
        - from_json
        - add_context
        - add_suggestion
        - _validate_error_code
        - _format_message
        - _serialize_details

## Derived Exception Classes

### JPYConfigurationError

::: jinpy_utils.base.JPYConfigurationError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table
      members:
        - __init__
        - __str__
        - __repr__

### JPYCacheError

::: jinpy_utils.base.JPYCacheError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table

### JPYDatabaseError

::: jinpy_utils.base.JPYDatabaseError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table

### JPYLoggingError

::: jinpy_utils.base.JPYLoggingError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table

### JPYValidationError

::: jinpy_utils.base.JPYValidationError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table

### JPYConnectionError

::: jinpy_utils.base.JPYConnectionError
    options:
      show_root_heading: true
      show_source: true
      show_signature_annotations: true
      show_bases: true
      docstring_section_style: table

## Usage Examples

### Basic Exception Usage

```python
from jinpy_utils.base import JPYConfigurationError

try:
    # Some operation that might fail
    if not api_key:
        raise JPYConfigurationError(
            message="API key is required",
            config_key="API_KEY",
            suggestions=[
                "Set the API_KEY environment variable",
                "Add api_key to your configuration file"
            ]
        )
except JPYConfigurationError as e:
    print(f"Configuration error: {e.message}")
    print(f"Config key: {e.config_key}")
    print(f"Suggestions: {', '.join(e.suggestions)}")
```

### JSON Serialization

```python
from jinpy_utils.base import JPYDatabaseError

try:
    # Database operation
    raise JPYDatabaseError(
        message="Connection timeout",
        database_name="user_db",
        table="users",
        operation="SELECT",
        timeout_seconds=30
    )
except JPYDatabaseError as e:
    # Convert to JSON for API response
    error_json = e.to_json()
    print(error_json)

    # Convert to dictionary for logging
    error_dict = e.to_dict()
    logger.error("Database operation failed", **error_dict)
```

### Validation Errors

```python
from jinpy_utils.base import JPYValidationError

def validate_user_input(data: dict):
    """Validate user input with detailed error reporting."""
    if not data.get("email"):
        raise JPYValidationError(
            message="Email is required",
            field="email",
            value=data.get("email"),
            validation_rule="required",
            suggestions=["Provide a valid email address"]
        )

    if "@" not in data.get("email", ""):
        raise JPYValidationError(
            message="Invalid email format",
            field="email",
            value=data["email"],
            validation_rule="email_format",
            expected_format="user@domain.com",
            suggestions=["Ensure email contains @ symbol and domain"]
        )

# Usage
try:
    validate_user_input({"email": "invalid-email"})
except JPYValidationError as e:
    print(f"Validation failed for field '{e.field}': {e.message}")
    print(f"Current value: '{e.value}'")
    print(f"Expected format: {e.expected_format}")
```

### Connection Errors with Retry Logic

```python
from jinpy_utils.base import JPYConnectionError
import time

def connect_with_retry(endpoint: str, max_retries: int = 3):
    """Connect to endpoint with retry logic and detailed error reporting."""
    for attempt in range(max_retries):
        try:
            # Simulated connection attempt
            if attempt < 2:  # Simulate failures
                raise JPYConnectionError(
                    message=f"Connection failed (attempt {attempt + 1})",
                    endpoint=endpoint,
                    protocol="HTTPS",
                    port=443,
                    timeout_seconds=30,
                    retry_count=attempt + 1,
                    max_retries=max_retries,
                    suggestions=[
                        "Check network connectivity",
                        "Verify endpoint URL",
                        "Check firewall settings"
                    ]
                )

            # Success case
            return "Connected successfully"

        except JPYConnectionError as e:
            if attempt == max_retries - 1:
                # Final failure
                e.add_context("final_attempt", True)
                e.add_suggestion("Contact system administrator")
                raise
            else:
                # Retry
                wait_time = 2 ** attempt
                time.sleep(wait_time)
                continue

# Usage
try:
    result = connect_with_retry("https://api.example.com")
except JPYConnectionError as e:
    print(f"Connection failed after {e.retry_count} attempts")
    print(f"Error: {e.message}")
    print(f"Suggestions: {', '.join(e.suggestions)}")
```

### Cache Errors

```python
from jinpy_utils.base import JPYCacheError

class CacheManager:
    """Example cache manager with structured error handling."""

    def get(self, key: str):
        """Get value from cache with error handling."""
        try:
            # Simulated cache operation
            if key.startswith("invalid_"):
                raise JPYCacheError(
                    message="Invalid cache key format",
                    cache_key=key,
                    operation="GET",
                    cache_type="redis",
                    expected_pattern="^[a-zA-Z0-9_-]+$",
                    suggestions=[
                        "Use only alphanumeric characters, underscores, and hyphens",
                        "Remove 'invalid_' prefix from key"
                    ]
                )

            # Return mock value
            return f"value_for_{key}"

        except JPYCacheError as e:
            # Log the error with structured data
            logger.error("Cache operation failed", **e.to_dict())
            raise

# Usage
cache = CacheManager()
try:
    value = cache.get("invalid_key_name!")
except JPYCacheError as e:
    print(f"Cache error: {e.message}")
    print(f"Operation: {e.operation} on key '{e.cache_key}'")
    print(f"Expected pattern: {e.expected_pattern}")
```

## Advanced Usage

### Exception Chaining

```python
from jinpy_utils.base import JPYDatabaseError, JPYConfigurationError

def connect_to_database():
    """Connect to database with proper exception chaining."""
    try:
        # Check configuration first
        if not database_url:
            raise JPYConfigurationError(
                message="Database URL not configured",
                config_key="DATABASE_URL"
            )

        # Attempt connection
        # ... connection code ...

    except ConnectionError as e:
        # Chain the original exception
        raise JPYDatabaseError(
            message="Failed to connect to database",
            database_url=database_url,
            original_error=str(e),
            suggestions=[
                "Check database server status",
                "Verify connection parameters",
                "Check network connectivity"
            ]
        ) from e
    except JPYConfigurationError:
        # Re-raise configuration errors as-is
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise JPYDatabaseError(
            message="Unexpected database error",
            original_error=str(e),
            error_type=type(e).__name__
        ) from e
```

### Context Management

```python
from contextlib import contextmanager
from jinpy_utils.base import JPYBaseException

@contextmanager
def error_context(operation: str, **context_data):
    """Add context to any jinpy exceptions that occur."""
    try:
        yield
    except JPYBaseException as e:
        # Add operation context to the exception
        e.add_context("operation", operation)
        for key, value in context_data.items():
            e.add_context(key, value)
        raise
    except Exception as e:
        # Wrap non-jinpy exceptions
        raise JPYBaseException(
            error_code="UNEXPECTED_ERROR",
            message=f"Unexpected error during {operation}",
            operation=operation,
            original_error=str(e),
            **context_data
        ) from e

# Usage
with error_context("user_registration", user_id=123, ip="192.168.1.1"):
    # Operations that might fail
    validate_user_data(user_data)
    save_user_to_database(user_data)
```

### Custom Exception Types

```python
from jinpy_utils.base import JPYBaseException

class JPYPaymentError(JPYBaseException):
    """Custom exception for payment-related errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            error_code="PAYMENT_ERROR",
            message=message,
            **kwargs
        )

class JPYAuthenticationError(JPYBaseException):
    """Custom exception for authentication errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            error_code="AUTHENTICATION_ERROR",
            message=message,
            **kwargs
        )

# Usage
def process_payment(amount: float, payment_method: str):
    """Process payment with custom error handling."""
    if amount <= 0:
        raise JPYPaymentError(
            message="Invalid payment amount",
            amount=amount,
            currency="USD",
            suggestions=["Amount must be greater than 0"]
        )

    if payment_method not in ["credit_card", "paypal", "bank_transfer"]:
        raise JPYPaymentError(
            message="Unsupported payment method",
            payment_method=payment_method,
            supported_methods=["credit_card", "paypal", "bank_transfer"],
            suggestions=["Use one of the supported payment methods"]
        )
```

### Error Recovery Patterns

```python
from jinpy_utils.base import JPYBaseException, JPYConnectionError, JPYCacheError

def robust_data_fetch(key: str):
    """Fetch data with multiple fallback strategies."""
    errors = []

    # Try cache first
    try:
        return cache.get(key)
    except JPYCacheError as e:
        errors.append(e)
        logger.warning("Cache fetch failed, trying database", error=e.to_dict())

    # Try database
    try:
        data = database.get(key)
        # Repopulate cache for next time
        try:
            cache.set(key, data)
        except JPYCacheError:
            pass  # Cache update failure is not critical
        return data
    except JPYConnectionError as e:
        errors.append(e)
        logger.warning("Database fetch failed, trying API", error=e.to_dict())

    # Try external API
    try:
        return api_client.fetch(key)
    except JPYConnectionError as e:
        errors.append(e)

        # All strategies failed
        raise JPYBaseException(
            error_code="DATA_FETCH_FAILED",
            message=f"Failed to fetch data for key '{key}' using all strategies",
            key=key,
            strategies_tried=["cache", "database", "api"],
            errors=[error.to_dict() for error in errors],
            suggestions=[
                "Check system connectivity",
                "Verify data exists",
                "Try again later"
            ]
        )
```

### Logging Integration

```python
from jinpy_utils.logger import get_logger
from jinpy_utils.base import JPYBaseException

logger = get_logger("exception_handler")

def handle_service_error(func):
    """Decorator for consistent service error handling."""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except JPYBaseException as e:
            # Log structured error data
            logger.error(
                f"Service error in {func.__name__}",
                function=func.__name__,
                **e.to_dict()
            )
            raise
        except Exception as e:
            # Log unexpected errors
            logger.error(
                f"Unexpected error in {func.__name__}",
                function=func.__name__,
                error_type=type(e).__name__,
                error_message=str(e)
            )
            # Convert to structured exception
            raise JPYBaseException(
                error_code="UNEXPECTED_SERVICE_ERROR",
                message=f"Unexpected error in {func.__name__}",
                function=func.__name__,
                original_error=str(e)
            ) from e
    return wrapper

# Usage
@handle_service_error
def user_service_operation(user_id: int):
    """Example service operation with error handling."""
    # Service logic that might raise exceptions
    pass
```

## Error Response Patterns

### API Response Format

```python
from flask import jsonify
from jinpy_utils.base import JPYBaseException

def create_error_response(error: JPYBaseException, status_code: int = 400):
    """Create standardized API error response."""
    response_data = {
        "error": {
            "code": error.error_code,
            "message": error.message,
            "timestamp": error.timestamp,
            "suggestions": error.suggestions
        }
    }

    # Add specific error details if available
    error_dict = error.to_dict()
    details = {k: v for k, v in error_dict.items()
               if k not in ["error_code", "message", "timestamp", "suggestions"]}

    if details:
        response_data["error"]["details"] = details

    return jsonify(response_data), status_code

# Usage in Flask route
@app.route("/api/users", methods=["POST"])
def create_user():
    try:
        # User creation logic
        return jsonify({"user": user_data}), 201
    except JPYBaseException as e:
        return create_error_response(e, 400)
    except Exception as e:
        # Convert unexpected errors
        error = JPYBaseException(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            original_error=str(e)
        )
        return create_error_response(error, 500)
```
