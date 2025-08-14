# Time Utilities API

Time-related utility functions.

## Time Functions

### get_current_datetime

::: jinpy_utils.utils.get_current_datetime
    options:
      show_source: true
      show_signature_annotations: true

## Usage Examples

### Basic Usage

```python
from jinpy_utils.utils import get_current_datetime

# Get current UTC datetime
now = get_current_datetime()
print(f"Current UTC time: {now}")
print(f"ISO format: {now.isoformat()}")

# The returned datetime is timezone-aware (UTC)
print(f"Timezone: {now.tzinfo}")  # UTC

# You can format it as needed
formatted = now.strftime("%Y-%m-%d %H:%M:%S UTC")
print(f"Formatted: {formatted}")
```

### Practical Examples

```python
from jinpy_utils.utils import get_current_datetime
import time

# Timing operations
start_time = get_current_datetime()
time.sleep(1.0)  # Simulate work
end_time = get_current_datetime()

duration = end_time - start_time
print(f"Operation took: {duration.total_seconds():.2f} seconds")

# Creating timestamps for logging
def log_with_timestamp(message: str):
    timestamp = get_current_datetime()
    print(f"[{timestamp.isoformat()}] {message}")

log_with_timestamp("Application started")
log_with_timestamp("Processing complete")
```

### Integration with Other Libraries

```python
from jinpy_utils.utils import get_current_datetime
from datetime import timedelta
import json

# Convert to different formats
now = get_current_datetime()

# For JSON serialization
data = {
    "event": "user_login",
    "timestamp": now.isoformat(),
    "user_id": 123
}
json_data = json.dumps(data)

# For database storage (many ORMs accept datetime objects directly)
user_record = {
    "created_at": now,
    "updated_at": now,
    "last_login": now
}

# Calculate relative times
one_hour_ago = now - timedelta(hours=1)
tomorrow = now + timedelta(days=1)

print(f"Now: {now}")
print(f"One hour ago: {one_hour_ago}")
print(f"Tomorrow: {tomorrow}")
```
