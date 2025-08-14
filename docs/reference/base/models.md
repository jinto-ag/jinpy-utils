# Base Models API

Data models and schemas used throughout jinpy-utils.

## Error Models

### ErrorDetails

::: jinpy_utils.base.ErrorDetails
    options:
      show_source: true
      show_signature_annotations: true
      members:
        - error_code
        - message
        - details
        - context
        - suggestions
        - timestamp
        - to_dict
        - from_dict
        - validate
        - add_context
        - add_suggestion

## Error Models Only

The base module only contains error-related models. Registry models are internal implementation details.

## Usage Examples

### ErrorDetails Usage

```python
from jinpy_utils.base import ErrorDetails
from datetime import datetime

# Create error details
error_details = ErrorDetails(
    error_code="VALIDATION_ERROR",
    message="Invalid input provided",
    details={
        "field": "email",
        "value": "invalid-email",
        "expected_format": "user@domain.com"
    },
    context={
        "request_id": "req_12345",
        "user_id": 123,
        "ip_address": "192.168.1.1"
    },
    suggestions=[
        "Provide a valid email address",
        "Check the email format"
    ],
    timestamp=datetime.utcnow()
)

# Add additional context
error_details.add_context("retry_count", 2)
error_details.add_suggestion("Contact support if problem persists")

# Convert to dictionary
error_dict = error_details.to_dict()
print(error_dict)

# Validate the error details
error_details.validate()
```

### Model Validation

```python
from jinpy_utils.base import ErrorDetails
from pydantic import ValidationError

try:
    # Invalid error details (missing required fields)
    invalid_details = ErrorDetails()
except ValidationError as e:
    print(f"Validation error: {e}")

# Valid error details
valid_details = ErrorDetails(
    error_code="TEST_ERROR",
    message="Test error message"
)

# Add context safely
valid_details.add_context("safe_key", "safe_value")
```

### Serialization and Deserialization

```python
import json
from jinpy_utils.base import ErrorDetails

# Create error details
original = ErrorDetails(
    error_code="SERIALIZATION_TEST",
    message="Testing serialization",
    details={"key": "value"},
    suggestions=["Try again"]
)

# Serialize to dictionary
error_dict = original.to_dict()

# Serialize to JSON
error_json = json.dumps(error_dict, default=str)

# Deserialize from dictionary
restored = ErrorDetails.from_dict(json.loads(error_json))

print(f"Original: {original.error_code}")
print(f"Restored: {restored.error_code}")
```

### Dynamic Model Creation

```python
from jinpy_utils.base import ErrorDetails
from typing import Dict, Any

def create_error_from_api_response(api_response: Dict[str, Any]) -> ErrorDetails:
    """Create ErrorDetails from API response."""
    return ErrorDetails(
        error_code=api_response.get("code", "UNKNOWN_ERROR"),
        message=api_response.get("message", "Unknown error occurred"),
        details=api_response.get("details", {}),
        context=api_response.get("context", {}),
        suggestions=api_response.get("suggestions", [])
    )


# Usage
api_response = {
    "code": "API_RATE_LIMIT",
    "message": "Rate limit exceeded",
    "details": {"limit": 1000, "window": 3600},
    "suggestions": ["Wait before retrying", "Upgrade to higher tier"]
}

error = create_error_from_api_response(api_response)
```

## Advanced Usage

### Model Inheritance

```python
from jinpy_utils.base import ErrorDetails
from pydantic import Field
from typing import Optional

class ExtendedErrorDetails(ErrorDetails):
    """Extended error details with additional fields."""

    severity: str = Field(default="medium", description="Error severity level")
    component: Optional[str] = Field(default=None, description="Component that generated the error")
    trace_id: Optional[str] = Field(default=None, description="Distributed tracing ID")

    def is_critical(self) -> bool:
        """Check if error is critical."""
        return self.severity in ["high", "critical"]

# Usage
extended_error = ExtendedErrorDetails(
    error_code="EXTENDED_ERROR",
    message="Extended error example",
    severity="high",
    component="user_service",
    trace_id="trace_12345"
)

print(f"Is critical: {extended_error.is_critical()}")
```

### Model Composition

```python
from jinpy_utils.base import ErrorDetails, RegistryMetadata
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ErrorReport(BaseModel):
    """Complete error report combining multiple models."""

    primary_error: ErrorDetails
    related_errors: List[ErrorDetails] = []
    registry_info: Optional[RegistryMetadata] = None
    reported_at: datetime = Field(default_factory=datetime.utcnow)
    reporter: Optional[str] = None
    environment: str = "unknown"

    def add_related_error(self, error: ErrorDetails):
        """Add a related error to the report."""
        self.related_errors.append(error)

    def get_all_error_codes(self) -> List[str]:
        """Get all error codes in this report."""
        codes = [self.primary_error.error_code]
        codes.extend([error.error_code for error in self.related_errors])
        return codes

# Usage
primary = ErrorDetails(
    error_code="PRIMARY_ERROR",
    message="Primary error occurred"
)

related = ErrorDetails(
    error_code="SECONDARY_ERROR",
    message="Secondary error occurred"
)

report = ErrorReport(
    primary_error=primary,
    reporter="user_service",
    environment="production"
)

report.add_related_error(related)
print(f"All error codes: {report.get_all_error_codes()}")
```

### Model Validation Hooks

```python
from jinpy_utils.base import ErrorDetails
from pydantic import validator, root_validator
from typing import Dict, Any

class ValidatedErrorDetails(ErrorDetails):
    """Error details with custom validation."""

    @validator('error_code')
    def validate_error_code(cls, v):
        """Validate error code format."""
        if not v or not isinstance(v, str):
            raise ValueError("Error code must be a non-empty string")

        if not v.isupper():
            raise ValueError("Error code must be uppercase")

        if not v.replace('_', '').isalnum():
            raise ValueError("Error code can only contain letters, numbers, and underscores")

        return v

    @validator('suggestions', each_item=True)
    def validate_suggestions(cls, v):
        """Validate each suggestion."""
        if not isinstance(v, str) or len(v.strip()) == 0:
            raise ValueError("Suggestions must be non-empty strings")
        return v.strip()

    @root_validator
    def validate_consistency(cls, values):
        """Validate consistency across fields."""
        error_code = values.get('error_code', '')
        message = values.get('message', '')

        # Ensure message is not just the error code
        if error_code and message.upper() == error_code:
            raise ValueError("Message should be more descriptive than just the error code")

        return values

# Usage
try:
    validated = ValidatedErrorDetails(
        error_code="test_error",  # Should be uppercase
        message="Test error"
    )
except ValueError as e:
    print(f"Validation error: {e}")

# Correct usage
validated = ValidatedErrorDetails(
    error_code="TEST_ERROR",
    message="This is a test error with proper description",
    suggestions=["Try again", "Check documentation"]
)
```

### Model Factory Pattern

```python
from jinpy_utils.base import ErrorDetails, RegistryMetadata
from typing import Dict, Any, Type
from abc import ABC, abstractmethod

class ModelFactory(ABC):
    """Abstract base class for model factories."""

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Any:
        pass

class ErrorDetailsFactory(ModelFactory):
    """Factory for creating ErrorDetails instances."""

    def create(self, data: Dict[str, Any]) -> ErrorDetails:
        """Create ErrorDetails from dictionary data."""
        # Apply default transformations
        if 'error_code' in data and not data['error_code'].isupper():
            data['error_code'] = data['error_code'].upper()

        # Ensure suggestions is a list
        if 'suggestions' in data and isinstance(data['suggestions'], str):
            data['suggestions'] = [data['suggestions']]

        return ErrorDetails(**data)

class MetadataFactory(ModelFactory):
    """Factory for creating RegistryMetadata instances."""

    def create(self, data: Dict[str, Any]) -> RegistryMetadata:
        """Create RegistryMetadata from dictionary data."""
        # Set defaults
        data.setdefault('category', 'general')
        data.setdefault('severity', 'medium')
        data.setdefault('retry_allowed', False)

        return RegistryMetadata(**data)

# Usage
error_factory = ErrorDetailsFactory()
metadata_factory = MetadataFactory()

error_data = {
    'error_code': 'validation_failed',  # Will be uppercased
    'message': 'Validation failed',
    'suggestions': 'Check input format'  # Will be converted to list
}

error = error_factory.create(error_data)
print(f"Error code: {error.error_code}")  # VALIDATION_FAILED
print(f"Suggestions: {error.suggestions}")  # ['Check input format']
```

### Model Caching

```python
from jinpy_utils.base import ErrorDetails
from functools import lru_cache
from typing import Dict, Any
import hashlib
import json

class CachedErrorDetails:
    """Cached error details for performance optimization."""

    @staticmethod
    @lru_cache(maxsize=1000)
    def create_cached(error_code: str, message: str, details_hash: str) -> ErrorDetails:
        """Create cached error details."""
        return ErrorDetails(
            error_code=error_code,
            message=message,
            details=json.loads(details_hash) if details_hash else {}
        )

    @classmethod
    def create(cls, error_code: str, message: str, details: Dict[str, Any] = None) -> ErrorDetails:
        """Create error details with caching."""
        details = details or {}
        details_hash = json.dumps(details, sort_keys=True) if details else ""

        return cls.create_cached(error_code, message, details_hash)

# Usage - repeated calls will use cached instances
error1 = CachedErrorDetails.create("CACHE_TEST", "Cache test message")
error2 = CachedErrorDetails.create("CACHE_TEST", "Cache test message")

print(f"Same instance: {error1 is error2}")  # True (cached)
```

## Model Integration

### Integration with Logging

```python
from jinpy_utils.base import ErrorDetails
from jinpy_utils.logger import get_logger

logger = get_logger("model_example")

def log_error_details(error: ErrorDetails):
    """Log error details in structured format."""
    logger.error(
        "Structured error occurred",
        **error.to_dict()
    )

# Usage
error = ErrorDetails(
    error_code="INTEGRATION_ERROR",
    message="Integration test error",
    context={"component": "payment_service", "version": "1.2.3"}
)

log_error_details(error)
```

### Integration with HTTP APIs

```python
from jinpy_utils.base import ErrorDetails
from typing import Dict, Any
import json

def error_to_http_response(error: ErrorDetails, status_code: int = 400) -> Dict[str, Any]:
    """Convert ErrorDetails to HTTP response format."""
    response = {
        "error": {
            "code": error.error_code,
            "message": error.message,
            "timestamp": error.timestamp.isoformat()
        },
        "status": status_code
    }

    if error.details:
        response["error"]["details"] = error.details

    if error.suggestions:
        response["error"]["suggestions"] = error.suggestions

    return response

def http_response_to_error(response_data: Dict[str, Any]) -> ErrorDetails:
    """Convert HTTP response to ErrorDetails."""
    error_data = response_data.get("error", {})

    return ErrorDetails(
        error_code=error_data.get("code", "HTTP_ERROR"),
        message=error_data.get("message", "HTTP request failed"),
        details=error_data.get("details", {}),
        suggestions=error_data.get("suggestions", [])
    )

# Usage
error = ErrorDetails(
    error_code="HTTP_VALIDATION_ERROR",
    message="Request validation failed"
)

http_response = error_to_http_response(error, 422)
restored_error = http_response_to_error(http_response)
```
