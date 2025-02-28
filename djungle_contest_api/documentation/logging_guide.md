# Djungle Contest API - Logging and Debugging Guide

This document provides comprehensive guidance on using the logging and debugging facilities within the Djungle Contest API.

## Overview

The Djungle Contest API includes a robust logging and debugging system designed to provide visibility into application behavior, assist with troubleshooting, and monitor system performance. The system supports different log levels, multiple output formats, and various debugging utilities.

## Logging Configuration

### Log Levels

The system uses standard Python logging levels:

- **DEBUG**: Detailed information, typically useful only for diagnosing problems
- **INFO**: Confirmation that things are working as expected
- **WARNING**: Indication that something unexpected happened, but the application is still working
- **ERROR**: Due to a more serious problem, the application may not perform some functions
- **CRITICAL**: A very serious error, indicating that the application may not be able to continue running

### Log Files

Logs are written to the following files in the `logs/` directory:

- `djungle_api.log`: General API requests and responses
- `contests.log`: Contest-specific operations
- `prize_distribution.log`: Detailed prize distribution logs
- `error.log`: All errors across the application

In production environments, these are rotating log files that will be automatically rotated when they reach 10MB in size, keeping 5 backups.

## How to Use Logging in Code

### Basic Logging

Each module should obtain a logger using:

```python
import logging
logger = logging.getLogger('contests.YOUR_MODULE')
```

Then use appropriate log levels:

```python
logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning")
logger.error("Error occurred")
logger.critical("Critical error")
```

### Logging with Context

To add contextual information to logs:

```python
context = {
    'contest_code': contest.code,
    'user_id': user_id
}
logger.info("Message with context", extra=context)
```

### Enabling Debug Mode

Debug mode can be enabled in several ways:

1. In settings.py by setting `DEBUG_MODE = True`
2. In API requests by adding `?debug=true` query parameter
3. In management commands with the `--debug` flag

## Debugging Utilities

The API includes specialized debugging utilities in the `contests.debug` module:

### Function Call Logging

Decorate functions to log their calls, arguments, and return values:

```python
from contests.debug import log_function_call

@log_function_call
def your_function(arg1, arg2):
    # Function implementation
    return result
```

### Performance Profiling

Profile function execution time and memory usage:

```python
from contests.debug import profile_function

@profile_function
def resource_intensive_function():
    # Implementation
    return result
```

### Debug Timers

Time specific code blocks:

```python
from contests.debug import DebugTimer

with DebugTimer("Database query operation"):
    # Code to time
    results = Model.objects.filter(...)
```

### Debug Printing

Print debug information only when in debug mode:

```python
from contests.debug import debug_print

debug_print("This will only be printed in debug mode", data)
```

## Middleware

The `LoggingContextMiddleware` automatically adds request-specific information to logs:

- Request ID (unique for each request)
- Client IP address
- User ID (if provided)
- Timestamp

## Configuring Logging for Development vs. Production

For development:
- Set `DEBUG = True` in settings.py
- Console logs will be verbose
- All log levels are recorded

For production:
- Set `DEBUG = False` in settings.py
- Console logs are restricted to WARNING and above
- Use structured JSON logging for easier parsing
- Configure email notifications for ERROR and CRITICAL logs

## Viewing Logs

### Console Output

When running the server in development mode, logs are output to the console with color-coding for different levels.

### File Logs

Log files are stored in the `logs/` directory. You can view them with:

```bash
tail -f logs/contests.log
```

### Log Analysis

For production environments, consider forwarding logs to a centralized logging system like ELK Stack (Elasticsearch, Logstash, Kibana) or Graylog.

## Troubleshooting Common Issues

### Missing Logs

1. Check that the `logs/` directory exists and is writable
2. Verify the logger name is correct
3. Ensure the log level is appropriate (DEBUG logs won't appear if level is set to INFO)

### Performance Issues with Logging

1. Avoid expensive logging operations in tight loops
2. Use lazy evaluation for complex log messages
3. Consider reducing log verbosity in production

## Best Practices

1. **Use appropriate log levels**: Don't log everything as ERROR
2. **Include context**: Add relevant IDs and state information
3. **Be concise**: Keep log messages clear and to the point
4. **Structured logging**: Use consistent formats for machine parsing
5. **Sensitive data**: Never log passwords, tokens, or personal information
6. **Exceptions**: Always log exceptions with tracebacks
7. **Performance**: Be mindful of the performance impact of detailed logging 