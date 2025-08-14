# Exception Registry API

Exception registry and factory functions for dynamic exception management.

## Registry Class

### ExceptionRegistry

::: jinpy_utils.base.ExceptionRegistry
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - register
        - get_exception_class
        - create_exception

## Factory Functions

### register_exception

::: jinpy_utils.base.register_exception
    options:
      show_source: true
      show_signature_annotations: true

### create_exception

::: jinpy_utils.base.create_exception
    options:
      show_source: true
      show_signature_annotations: true

## Usage Examples

### Basic Registry Usage

```python
from jinpy_utils.base import (
    JPYBaseException,
    register_exception,
    create_exception,
    get_exception_class
)

# Define custom exception
class JPYPaymentError(JPYBaseException):
    """Exception for payment processing errors."""

    def __init__(self, message: str, **kwargs):
        super().__init__(
            error_code="PAYMENT_ERROR",
            message=message,
            **kwargs
        )

# Register the exception
register_exception("PAYMENT_ERROR", JPYPaymentError)

# Create exception instances using the registry
payment_error = create_exception(
    "PAYMENT_ERROR",
    message="Credit card declined",
    card_type="Visa",
    decline_reason="insufficient_funds"
)

# Get exception class from registry
PaymentErrorClass = get_exception_class("PAYMENT_ERROR")
another_error = PaymentErrorClass(message="Payment timeout")
```

### Advanced Registration

```python
from jinpy_utils.base import register_exception, JPYBaseException

class JPYCustomError(JPYBaseException):
    """Custom application error with specific handling."""

    def __init__(self, message: str, severity: str = "medium", **kwargs):
        super().__init__(
            error_code="CUSTOM_ERROR",
            message=message,
            severity=severity,
            **kwargs
        )

    @property
    def is_critical(self) -> bool:
        """Check if error is critical."""
        return self.severity == "critical"

# Register with custom metadata
register_exception(
    error_code="CUSTOM_ERROR",
    exception_class=JPYCustomError,
    metadata={
        "category": "application",
        "severity_levels": ["low", "medium", "high", "critical"],
        "description": "Custom application-specific error"
    }
)

# Create with specific severity
critical_error = create_exception(
    "CUSTOM_ERROR",
    message="System failure detected",
    severity="critical",
    component="database",
    action_required="immediate_attention"
)

print(f"Is critical: {critical_error.is_critical}")
```

### Dynamic Error Handling

```python
from jinpy_utils.base import create_exception, list_registered_exceptions

def handle_error_by_code(error_code: str, **error_data):
    """Create and handle errors dynamically based on error code."""
    try:
        error = create_exception(error_code, **error_data)

        # Handle based on error type
        if error_code.startswith("PAYMENT_"):
            handle_payment_error(error)
        elif error_code.startswith("AUTH_"):
            handle_auth_error(error)
        else:
            handle_generic_error(error)

    except ValueError as e:
        print(f"Unknown error code: {error_code}")
        print(f"Registered codes: {list_registered_exceptions()}")

def handle_payment_error(error):
    """Handle payment-specific errors."""
    print(f"Payment Error: {error.message}")
    # Specific payment error handling

def handle_auth_error(error):
    """Handle authentication errors."""
    print(f"Auth Error: {error.message}")
    # Specific auth error handling

def handle_generic_error(error):
    """Handle generic errors."""
    print(f"Generic Error: {error.message}")
    # Generic error handling

# Usage
error_data = {
    "message": "Transaction declined",
    "transaction_id": "tx_12345",
    "amount": 99.99
}

handle_error_by_code("PAYMENT_ERROR", **error_data)
```

### Registry Management

```python
from jinpy_utils.base import (
    ExceptionRegistry,
    JPYBaseException,
    list_registered_exceptions
)

# Create custom registry for specific module
module_registry = ExceptionRegistry()

class ModuleSpecificError(JPYBaseException):
    """Module-specific error."""
    pass

# Register to custom registry
module_registry.register("MODULE_ERROR", ModuleSpecificError)

# Check registration
print("Global registry:", list_registered_exceptions())
print("Module registry:", module_registry.list_registered())

# Create from custom registry
module_error = module_registry.create_exception(
    "MODULE_ERROR",
    message="Module operation failed"
)
```

### Error Code Validation

```python
from jinpy_utils.base import register_exception, JPYBaseException
import re

class JPYApiError(JPYBaseException):
    """API-related error with code validation."""

    def __init__(self, message: str, **kwargs):
        # Validate error code format
        if not re.match(r"^API_[A-Z_]+$", kwargs.get("error_code", "")):
            kwargs["error_code"] = "API_GENERIC_ERROR"

        super().__init__(message=message, **kwargs)

# Register API errors with validation
api_error_codes = [
    "API_RATE_LIMIT_EXCEEDED",
    "API_INVALID_TOKEN",
    "API_RESOURCE_NOT_FOUND",
    "API_SERVER_ERROR"
]

for code in api_error_codes:
    register_exception(code, JPYApiError)

# Usage with automatic validation
try:
    error = create_exception(
        "API_RATE_LIMIT_EXCEEDED",
        message="Rate limit exceeded",
        limit=1000,
        window_seconds=3600
    )
except ValueError as e:
    print(f"Invalid error code: {e}")
```

### Configuration-Based Registration

```python
import yaml
from jinpy_utils.base import register_exception, JPYBaseException

# Error configuration file
error_config = """
errors:
  PAYMENT_DECLINED:
    class: JPYPaymentError
    category: payment
    severity: high
    retry_allowed: false

  NETWORK_TIMEOUT:
    class: JPYConnectionError
    category: network
    severity: medium
    retry_allowed: true
    max_retries: 3

  INVALID_INPUT:
    class: JPYValidationError
    category: validation
    severity: low
    retry_allowed: false
"""

class ErrorManager:
    """Manage errors from configuration."""

    def __init__(self, config_path: str = None, config_data: str = None):
        if config_data:
            self.config = yaml.safe_load(config_data)
        elif config_path:
            with open(config_path) as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {"errors": {}}

    def register_all_errors(self):
        """Register all errors from configuration."""
        for error_code, error_config in self.config["errors"].items():
            exception_class = self._get_exception_class(error_config["class"])

            register_exception(
                error_code=error_code,
                exception_class=exception_class,
                metadata={
                    "category": error_config.get("category"),
                    "severity": error_config.get("severity"),
                    "retry_allowed": error_config.get("retry_allowed", False),
                    "max_retries": error_config.get("max_retries", 0)
                }
            )

    def _get_exception_class(self, class_name: str):
        """Get exception class by name."""
        # Map class names to actual classes
        class_map = {
            "JPYPaymentError": JPYPaymentError,
            "JPYConnectionError": JPYConnectionError,
            "JPYValidationError": JPYValidationError
        }

        return class_map.get(class_name, JPYBaseException)

# Initialize and register errors
error_manager = ErrorManager(config_data=error_config)
error_manager.register_all_errors()

# Use configured errors
payment_error = create_exception(
    "PAYMENT_DECLINED",
    message="Credit card was declined",
    card_number="****1234"
)
```

### Error Registry Inspection

```python
from jinpy_utils.base import (
    list_registered_exceptions,
    get_exception_class,
    ExceptionRegistry
)

def inspect_registry():
    """Inspect the current exception registry."""
    registered = list_registered_exceptions()

    print(f"Total registered exceptions: {len(registered)}")

    for error_code in registered:
        exception_class = get_exception_class(error_code)

        print(f"\nError Code: {error_code}")
        print(f"  Class: {exception_class.__name__}")
        print(f"  Module: {exception_class.__module__}")

        # Check if class has documentation
        if exception_class.__doc__:
            print(f"  Description: {exception_class.__doc__.strip()}")

        # Check for custom methods
        custom_methods = [
            method for method in dir(exception_class)
            if not method.startswith('_') and
               method not in dir(JPYBaseException)
        ]

        if custom_methods:
            print(f"  Custom methods: {', '.join(custom_methods)}")

inspect_registry()
```

### Thread-Safe Registry Usage

```python
import threading
from jinpy_utils.base import register_exception, create_exception, JPYBaseException

class ThreadSafeErrorHandler:
    """Thread-safe error handling using registry."""

    def __init__(self):
        self.lock = threading.Lock()
        self.error_counts = {}

    def register_error_type(self, error_code: str, exception_class):
        """Thread-safe error registration."""
        with self.lock:
            register_exception(error_code, exception_class)
            self.error_counts[error_code] = 0

    def create_and_count_error(self, error_code: str, **kwargs):
        """Create error and increment counter thread-safely."""
        with self.lock:
            self.error_counts[error_code] = self.error_counts.get(error_code, 0) + 1

        return create_exception(error_code, **kwargs)

    def get_error_stats(self) -> dict:
        """Get error statistics thread-safely."""
        with self.lock:
            return self.error_counts.copy()

# Usage in multithreaded environment
error_handler = ThreadSafeErrorHandler()

class ThreadSpecificError(JPYBaseException):
    pass

error_handler.register_error_type("THREAD_ERROR", ThreadSpecificError)

def worker_function(worker_id: int):
    """Worker function that might generate errors."""
    try:
        # Some work that might fail
        if worker_id % 3 == 0:  # Simulate occasional errors
            error = error_handler.create_and_count_error(
                "THREAD_ERROR",
                message=f"Error in worker {worker_id}",
                worker_id=worker_id
            )
            raise error
    except ThreadSpecificError as e:
        print(f"Worker {worker_id} error: {e.message}")

# Run multiple threads
threads = []
for i in range(10):
    thread = threading.Thread(target=worker_function, args=(i,))
    threads.append(thread)
    thread.start()

for thread in threads:
    thread.join()

print("Error statistics:", error_handler.get_error_stats())
```

## Registry Best Practices

### Namespace Organization

```python
from jinpy_utils.base import register_exception, JPYBaseException

# Organize errors by namespace/module
class UserServiceError(JPYBaseException):
    pass

class PaymentServiceError(JPYBaseException):
    pass

class NotificationServiceError(JPYBaseException):
    pass

# Register with namespaced codes
service_errors = {
    "USER_INVALID_EMAIL": UserServiceError,
    "USER_DUPLICATE_USERNAME": UserServiceError,
    "PAYMENT_CARD_DECLINED": PaymentServiceError,
    "PAYMENT_INSUFFICIENT_FUNDS": PaymentServiceError,
    "NOTIFICATION_DELIVERY_FAILED": NotificationServiceError,
    "NOTIFICATION_INVALID_TEMPLATE": NotificationServiceError
}

for error_code, exception_class in service_errors.items():
    register_exception(error_code, exception_class)
```

### Registry Cleanup

```python
from jinpy_utils.base import unregister_exception, list_registered_exceptions

def cleanup_module_errors(module_prefix: str):
    """Clean up errors for a specific module."""
    registered = list_registered_exceptions()

    for error_code in registered:
        if error_code.startswith(module_prefix):
            unregister_exception(error_code)
            print(f"Unregistered: {error_code}")

# Clean up test errors after testing
cleanup_module_errors("TEST_")
```

### Error Code Documentation

```python
from jinpy_utils.base import register_exception, JPYBaseException

class DocumentedError(JPYBaseException):
    """
    Well-documented error class with usage examples.

    This error should be used when specific business logic fails.

    Example:
        error = DocumentedError(
            message="Operation failed",
            operation_type="user_creation",
            failure_reason="validation_failed"
        )
    """

    ERROR_CODE = "DOCUMENTED_ERROR"

    def __init__(self, message: str, operation_type: str = None, **kwargs):
        super().__init__(
            error_code=self.ERROR_CODE,
            message=message,
            operation_type=operation_type,
            **kwargs
        )

register_exception(
    DocumentedError.ERROR_CODE,
    DocumentedError,
    metadata={
        "description": DocumentedError.__doc__,
        "required_fields": ["message"],
        "optional_fields": ["operation_type"],
        "usage_examples": [
            "User validation failures",
            "Business rule violations",
            "Workflow state errors"
        ]
    }
)
```
