# Testing Guide for Djungle Contest API

This guide provides instructions for running the test suites and understanding test coverage for the Djungle Contest API.

## Table of Contents

- [Testing Guide for Djungle Contest API](#testing-guide-for-djungle-contest-api)
  - [Table of Contents](#table-of-contents)
  - [Overview of Test Suite](#overview-of-test-suite)
  - [Test Structure](#test-structure)
  - [Running the Tests](#running-the-tests)
    - [Using Django's Test Runner](#using-djangos-test-runner)
    - [Using the Custom Test Runner](#using-the-custom-test-runner)
  - [Test Reports](#test-reports)
  - [Docker-based Testing](#docker-based-testing)
  - [Continuous Integration](#continuous-integration)
  - [Test Coverage](#test-coverage)
  - [Writing New Tests](#writing-new-tests)

## Overview of Test Suite

The test suite for Djungle Contest API includes:

- **Unit Tests**: Testing individual components in isolation
- **Integration Tests**: Testing interactions between components
- **Functional Tests**: Testing entire features from a user perspective
- **Time-based Tests**: Testing time-dependent features using mock time

All tests follow Django's testing framework conventions, using the `TestCase` class to provide database isolation and transaction support.

## Test Structure

Tests are organized in the following structure:

```
contests/
├── tests/
│   ├── __init__.py              # Makes tests discoverable
│   ├── test_contest_management.py  # Tests for Contest model CRUD operations
│   ├── test_prize_distribution.py  # Tests for prize distribution algorithm
│   ├── test_api_endpoints.py    # Tests for API endpoints and status codes
│   ├── test_win_records.py      # Tests for win record tracking
│   └── test_logging.py          # Tests for logging implementation
├── test_prize_distribution.py   # Standalone prize distribution testing script
└── tests.py                     # Legacy tests file
```

Additionally, there are standalone test scripts in the project root:

```
djungle_contest_api/
├── run_tests.py                 # Test runner with reporting capabilities
├── test_api.py                  # Manual API testing script
└── test_prize_distribution.py   # Manual prize distribution testing script
```

## Running the Tests

### Using Django's Test Runner

To run all tests using Django's built-in test runner:

```bash
python manage.py test contests
```

To run specific test modules:

```bash
python manage.py test contests.tests.test_api_endpoints
```

To run a specific test class:

```bash
python manage.py test contests.tests.test_api_endpoints.PlayEndpointTests
```

To run a specific test method:

```bash
python manage.py test contests.tests.test_api_endpoints.PlayEndpointTests.test_valid_contest
```

### Using the Custom Test Runner

We've provided a custom test runner with enhanced reporting:

```bash
python run_tests.py
```

Options available with the custom runner:

```bash
python run_tests.py -v 2              # Run with verbose output
python run_tests.py -r                # Generate a detailed report
python run_tests.py -o report.txt     # Save report to a file
python run_tests.py contests.tests.test_api_endpoints  # Run specific tests
```

## Test Reports

The custom test runner generates detailed reports including:

- Total tests run
- Number of failures and errors
- Test duration
- Success/failure status

Example report:

```
================================================================================
Djungle Contest API Test Report - 2023-04-25 14:30:45
================================================================================
Tests run: 42
Failures: 0
Errors: 0
Skipped: 0
Expected failures: 0
Unexpected successes: 0
Duration: 0m 23s
--------------------------------------------------------------------------------
Result: SUCCESS
================================================================================
```

## Docker-based Testing

To run tests in a Docker environment (recommended for CI/CD):

```bash
# Build the testing container
docker-compose build web

# Run tests
docker-compose run --rm web python manage.py test contests

# Run tests with the custom runner
docker-compose run --rm web python run_tests.py -r
```

## Continuous Integration

The test suite is designed to run in CI environments. Key considerations:

1. Tests are fast and isolated to avoid flaky test issues
2. Time-dependent tests use mocking to ensure consistency
3. Database state is reset between test cases

## Test Coverage

To generate a test coverage report, install the `coverage` package and run:

```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='contests' manage.py test contests

# Generate report
coverage report

# Generate HTML report
coverage html
```

View the HTML report by opening `htmlcov/index.html` in a browser.

## Writing New Tests

When writing new tests, follow these guidelines:

1. **Isolation**: Each test should be independent and not rely on the state from other tests
2. **Naming**: Use descriptive names that explain what's being tested
3. **Docstrings**: Include docstrings that explain the purpose of each test
4. **Assertions**: Use specific assertions rather than generic ones
5. **Mocking**: Use `mock.patch` for time-dependent features

Example test structure:

```python
def test_feature_specific_condition(self):
    """Test that feature X behaves correctly under condition Y."""
    # Setup phase - prepare test data
    # ...
    
    # Exercise phase - call the function under test
    result = function_under_test()
    
    # Verify phase - assert expected outcomes
    self.assertEqual(result, expected_value)
    
    # Cleanup phase (usually handled by TestCase)
```

For time-based tests, use Django's timezone mocking:

```python
from unittest import mock
from django.utils import timezone

@mock.patch('django.utils.timezone.now')
def test_time_dependent_feature(self, mock_now):
    # Set a specific time
    mock_date = timezone.now().replace(hour=8, minute=0)
    mock_now.return_value = mock_date
    
    # Now any code using timezone.now() will use your mocked time
    result = function_that_uses_current_time()
    self.assertEqual(result, expected_value)
``` 