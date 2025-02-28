# Logging Troubleshooting Guide

## Common Issues

### KeyError: 'request_id' in Logs

**Issue:** When starting the Django server or in other non-request contexts, you might encounter an error like this:

```
KeyError: 'request_id'
ValueError: Formatting field not found in record: 'request_id'
```

**Cause:** 
This occurs because our logging configuration uses request-specific context variables (`request_id`, `client_ip`, `user_id`) in formatters, but these variables are only available within the context of an HTTP request. When Django logs messages outside of a request context (e.g., during startup or in background tasks), these fields aren't available.

**Solution:**
The issue has been fixed by:

1. Adding a `LoggingContextFilter` to handlers that use request-specific context:
   ```python
   'filters': {
       'add_request_context': {
           '()': 'contests.middleware.LoggingContextFilter',
       },
   },
   ```

2. Applying this filter to handlers that need request context:
   ```python
   'file_api': {
       # ... other config ...
       'filters': ['add_request_context'],
   },
   ```

3. Updating the `LoggingContextFilter` to provide default values for missing context:
   ```python
   def filter(self, record):
       if not hasattr(record, 'request_id'):
           record.request_id = getattr(local, 'request_id', 'no-request-id')
       
       if not hasattr(record, 'client_ip'):
           record.client_ip = getattr(local, 'client_ip', 'unknown')
       
       if not hasattr(record, 'user_id'):
           record.user_id = getattr(local, 'user_id', 'anonymous')
       
       return True
   ```

### Other Logging Issues

#### Logs Not Being Written

If logs aren't being written to the expected files:

1. Check that the `logs` directory exists and has the correct permissions
2. Verify that the logging level is appropriate for the messages you're trying to log
3. Ensure that the logger name used in your code matches what's defined in settings

#### Performance Issues with Logging

If logging is causing performance problems:

1. Adjust log levels to reduce the volume of logs (e.g., use INFO instead of DEBUG in production)
2. Consider using asynchronous logging for high-volume environments
3. Implement log rotation to prevent large log files from impacting performance

## Logging Best Practices

1. **Use Appropriate Log Levels**
   - `DEBUG`: Detailed information, typically useful only for diagnosing problems
   - `INFO`: Confirmation that things are working as expected
   - `WARNING`: An indication that something unexpected happened, but the application is still working
   - `ERROR`: Due to a more serious problem, the application has not been able to perform a function
   - `CRITICAL`: A serious error, indicating that the application itself may be unable to continue running

2. **Include Context in Log Messages**
   - Always include enough context to understand what happened
   - Consider including request IDs for traceability
   - For errors, include relevant exception information

3. **Structure Logs for Analysis**
   - Use consistent formatting
   - Consider using JSON formatting for machine parsing
   - Include timestamps, severity, and source information

4. **Log Rotation**
   - Configure log rotation to prevent disks from filling up
   - Archive old logs for historical analysis

## Docker Logging Considerations

When running the application in Docker:

1. Use the `/app/logs` volume mapping to persist logs outside the container
2. Consider using a logging driver like `json-file` with proper size limits
3. For production, consider forwarding logs to a centralized logging system 