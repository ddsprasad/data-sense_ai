# DataSense Logging System Guide

## Overview

DataSense now includes a comprehensive logging system that captures application events, API requests, SQL queries, errors, and performance metrics.

---

## Log Files

All logs are stored in the `logs/` directory:

| File | Purpose | Max Size | Backups |
|------|---------|----------|---------|
| `datasense.log` | General application logs | 10MB | 5 |
| `error.log` | Errors and critical issues only | 10MB | 5 |
| `api_requests.log` | API request/response logs | 20MB | 10 |
| `sql_queries.log` | SQL query execution logs | 15MB | 7 |
| `performance.log` | Performance metrics & slow requests | 10MB | 5 |

**Format:** All logs use JSON formatting for easy parsing and analysis.

---

## Log Levels

| Level | When to Use |
|-------|-------------|
| `DEBUG` | Detailed diagnostic information |
| `INFO` | General informational messages |
| `WARNING` | Warning messages (non-critical) |
| `ERROR` | Error messages (handled exceptions) |
| `CRITICAL` | Critical errors (system failures) |

**Default:** `INFO` (configurable via `LOG_LEVEL` environment variable)

---

## Configuration

### Environment Variables

```bash
# Set log level
export LOG_LEVEL=DEBUG  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Enable request body logging (caution: may log sensitive data)
export LOG_REQUEST_BODIES=true
```

### Code Configuration

Edit `main.py` to customize logging:

```python
setup_logging(
    log_dir="logs",
    log_level="INFO",              # Change log level
    enable_console=True,            # Console output
    enable_json=True,               # JSON formatting
    enable_colored_console=True     # Colored console output
)
```

---

## Usage Examples

### Basic Logging

```python
from logging_setup.logging_config import get_logger

logger = get_logger(__name__)

logger.info("Processing user request")
logger.warning("Rate limit approaching")
logger.error("Failed to connect to database", exc_info=True)
```

### Logging with Context

```python
logger.info(
    "User logged in",
    extra={
        'user_id': 12345,
        'session_id': 'abc-123',
        'ip_address': '192.168.1.1'
    }
)
```

### API Logging

API requests are automatically logged by the middleware:

```json
{
  "timestamp": "2025-01-22T10:30:45.123Z",
  "level": "INFO",
  "message": "Request: POST /v2/original-question",
  "endpoint": "/v2/original-question",
  "method": "POST",
  "client_ip": "192.168.1.100",
  "status_code": 200,
  "execution_time": 234.56,
  "user_id": 300
}
```

### SQL Query Logging

```python
from logging_setup.logging_config import log_sql_query

log_sql_query(
    query="SELECT * FROM dim_member WHERE user_id = ?",
    execution_time=45.2,
    rows_affected=1,
    user_id=300,
    question_id="abc-123"
)
```

### Performance Logging

```python
from logging_setup.logging_config import log_performance_metric

log_performance_metric(
    operation="vector_search",
    duration_ms=128.5,
    metadata={'query_length': 50, 'results_count': 10}
)
```

---

## Log Structure

### JSON Log Format

```json
{
  "timestamp": "2025-01-22T10:30:45.123456",
  "level": "INFO",
  "logger": "main",
  "message": "Request completed successfully",
  "module": "main",
  "function": "answer_original_question",
  "line": 142,
  "endpoint": "/v2/original-question",
  "status_code": 200,
  "execution_time_ms": 234.56,
  "user_id": 300,
  "question_id": "abc-123-def-456"
}
```

---

## Middleware Features

### 1. Request/Response Logging
- Automatically logs all API requests
- Captures method, endpoint, client IP, status code
- Measures execution time
- Adds `X-Execution-Time` header to responses

### 2. Performance Monitoring
- Logs slow requests (> 1000ms by default)
- Helps identify performance bottlenecks
- Configurable threshold

### 3. Error Logging
- Automatically logs all exceptions
- Includes stack traces
- Preserves error context

---

## Analyzing Logs

### View Recent Logs

```bash
# Last 100 lines of general log
tail -100 logs/datasense.log

# Follow error log in real-time
tail -f logs/error.log

# View today's API requests
grep "$(date +%Y-%m-%d)" logs/api_requests.log
```

### Parse JSON Logs

```bash
# Pretty print JSON logs
cat logs/datasense.log | jq '.'

# Filter by log level
cat logs/datasense.log | jq 'select(.level == "ERROR")'

# Filter by user
cat logs/api_requests.log | jq 'select(.user_id == 300)'

# Show slow requests
cat logs/performance.log | jq 'select(.execution_time > 1000)'
```

### Common Queries

**Find all errors in last hour:**
```bash
cat logs/error.log | jq 'select(.timestamp > "'$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S)'")'
```

**Top 10 slowest endpoints:**
```bash
cat logs/api_requests.log | jq -r '"\(.execution_time) \(.endpoint)"' | sort -rn | head -10
```

**Count requests by endpoint:**
```bash
cat logs/api_requests.log | jq -r '.endpoint' | sort | uniq -c | sort -rn
```

---

## Log Rotation

Logs automatically rotate when they exceed their max size:

- Old logs are renamed with `.1`, `.2`, `.3`, etc.
- Example: `datasense.log.1`, `datasense.log.2`
- Oldest logs are deleted when backup count is exceeded

---

## Best Practices

### DO:
✅ Use appropriate log levels
✅ Include context (user_id, question_id, etc.)
✅ Log business-critical operations
✅ Log performance metrics for slow operations
✅ Log errors with stack traces

### DON'T:
❌ Log sensitive data (passwords, API keys, PII)
❌ Log excessively in tight loops
❌ Use `print()` statements (use logger instead)
❌ Log entire request bodies without sanitization
❌ Ignore log rotation (large logs slow down parsing)

---

## Monitoring & Alerts

### Set Up Log Monitoring

Consider integrating with log management tools:

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Splunk**
- **Datadog**
- **CloudWatch** (AWS)
- **Azure Monitor**

### Example: Send Errors to Slack

```python
import requests

class SlackErrorHandler(logging.Handler):
    def emit(self, record):
        if record.levelno >= logging.ERROR:
            requests.post(
                'https://hooks.slack.com/your-webhook',
                json={'text': f"🚨 Error: {record.getMessage()}"}
            )

# Add to error logger
error_logger = logging.getLogger('error')
error_logger.addHandler(SlackErrorHandler())
```

---

## Troubleshooting

### Logs Not Appearing

1. **Check log level:** Ensure `LOG_LEVEL` is set correctly
2. **Check permissions:** Ensure `logs/` directory is writable
3. **Check handlers:** Verify handlers are configured in `logging_config.py`

### Log Files Too Large

1. **Reduce log level:** Use `WARNING` or `ERROR` instead of `INFO`/`DEBUG`
2. **Decrease backup count:** Fewer historical logs
3. **Archive old logs:** Move old logs to separate storage

### Performance Impact

Logging has minimal performance impact:
- JSON formatting: ~0.1-0.5ms per log entry
- File I/O: Buffered, non-blocking
- Typical overhead: < 1% of request time

---

## Integration with Existing Code

### Replace print() Statements

**Before:**
```python
print("Connected to database successfully!")
print(f"Error: {e}")
```

**After:**
```python
logger.info("Connected to database successfully!")
logger.error(f"Error: {e}", exc_info=True)
```

### Update Database Logging

The existing database logging (`Executions` table) is preserved.
File logging provides additional visibility and debugging capabilities.

---

## Security

### Log Sanitization

Sensitive fields are automatically masked in request body logging:

```python
# Automatically masked fields:
- password
- token
- api_key
- secret
- credential
```

### Access Control

Restrict access to log files:

```bash
chmod 640 logs/*.log  # Owner read/write, group read, no public access
```

---

## Maintenance

### Weekly Tasks
- Review error logs
- Check for recurring issues
- Analyze slow requests

### Monthly Tasks
- Archive old logs
- Review log retention policy
- Update log analysis queries

---

## Examples

### Complete Endpoint Logging Example

```python
from logging_setup.logging_config import get_logger, log_performance_metric
import time

logger = get_logger(__name__)

@app.post("/v2/my-endpoint")
def my_endpoint(data: RequestModel, user_id: int):
    start_time = time.time()

    try:
        logger.info(
            "Processing request",
            extra={'user_id': user_id, 'data_size': len(str(data))}
        )

        # Your logic here
        result = process_data(data)

        # Log performance
        duration = (time.time() - start_time) * 1000
        log_performance_metric(
            operation="my_endpoint",
            duration_ms=duration,
            metadata={'user_id': user_id}
        )

        logger.info("Request completed successfully")
        return result

    except Exception as e:
        logger.error(
            f"Request failed: {str(e)}",
            extra={'user_id': user_id},
            exc_info=True
        )
        raise
```

---

## Support

For questions or issues with logging:
1. Check this guide
2. Review `config/logging_config.py`
3. Check middleware implementation in `middleware/logging_middleware.py`

---

**Last Updated:** 2025-01-22
**Version:** 1.0.0
