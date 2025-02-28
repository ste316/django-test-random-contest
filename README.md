# Djungle Contest API

A Django-based API for managing contests where players participate in a pseudo-random prize extraction game.

## Project Overview

The Djungle Contest API allows users to participate in contests and win prizes based on a pseudo-random algorithm. The system supports multiple contests running concurrently, with each contest offering prizes that can be won several times per day.

## Features

- Contest management with validity date ranges
- Prize configuration with daily winning limits
- Pseudo-random prize extraction algorithm
- API endpoint for contest participation
- Admin interface for managing contests and prizes

## Prerequisites

- Docker
- Docker Compose

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd djungle_contest_api
   ```

2. Build and start the Docker containers:
   ```bash
   docker-compose up --build
   ```

3. Run database migrations (if needed):
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. Create a superuser:
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. Access the application:
   - API: http://localhost:8000/play/
   - Admin Interface: http://localhost:8000/admin/

## Running Tests

The project includes multiple testing approaches:

### Django Unit Tests

Run Django's built-in test suite for the contests app:
```bash
docker-compose exec web python manage.py test contests.tests
```

### Basic Test Script

The project includes a comprehensive test script `basic_test.py` for testing the API endpoint.

### Running Tests Locally

1. Ensure the application is running in Docker
2. Run the tests:
   ```bash
   # Basic test script
   docker-compose exec web python basic_test.py
   ```

### Test Scenarios Covered

#### Django Unit Tests
- Model validation
- View logic
- Utility function testing

#### Basic Test Script
- Participating in a contest with an anonymous user
- Multiple requests with the same user
- Multiple anonymous requests
- Handling invalid contest codes
- Handling missing contest parameters
- Debug mode testing

## Project Structure

- `contests/models.py`: Contains the Contest, Prize, and WinRecord models
- `contests/views.py`: Contains the API endpoint implementation
- `contests/utils.py`: Contains utility functions for the prize extraction algorithm
- `basic_test.py`: Comprehensive test script for the /play endpoint

## License

[License information]

## Prize Distribution System

The Djungle Contest API includes a sophisticated prize distribution system that ensures fair and even distribution of prizes throughout the day. The system is designed to:

1. Respect daily prize limits defined for each prize
2. Distribute prizes evenly throughout the day
3. Adapt to current distribution patterns to correct imbalances
4. Provide detailed statistics and visualization tools

### Key Features

- Advanced probability-based distribution algorithm
- Time-weighted distribution patterns favoring business hours
- Real-time monitoring of distribution quality
- Detailed statistics for analyzing prize distribution
- Visualization tools for easy monitoring

### API Endpoints

#### Play Endpoint

```
GET /play/?contest={code}&user={user_id}
```

Allows users to participate in a contest for a chance to win a prize.

### Management Commands

The system includes several management commands for administrators:

```bash
# Analyze prize distribution for a contest
python manage.py analyze_prize_distribution CONTEST_CODE
``` 