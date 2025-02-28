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

## Setup Instructions

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd djungle_contest_api
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/Scripts/activate  # On Windows
   # OR
   source venv/bin/activate  # On Unix/MacOS
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Apply migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

7. Access the admin interface at http://127.0.0.1:8000/admin/

## API Endpoints

### GET /play/

Endpoint for participating in a contest.

**Parameters:**
- `contest`: (Required) The contest code to participate in.
- `user`: (Optional) User identifier for tracking wins per user (bonus feature).

**Responses:**
- HTTP 400: Contest code is missing.
- HTTP 404: Contest code is not found.
- HTTP 422: Contest is not active (outside the valid date range).
- HTTP 200: Response with winning or non-winning result.

## Project Structure

- `contests/models.py`: Contains the Contest, Prize, and WinRecord models.
- `contests/views.py`: Contains the API endpoint implementation.
- `contests/utils.py`: Contains utility functions for the prize extraction algorithm.

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

Allows users to participate in a contest with a chance to win prizes based on the fair distribution algorithm.

#### Statistics Endpoint

```
GET /stats/?contest={code}&prize={prize_code}
```

Provides detailed statistics about prize distribution for a contest or specific prize.

### Management Commands

The system includes several management commands for administrators:

```bash
# Analyze prize distribution for a contest
python manage.py analyze_prize_distribution CONTEST_CODE

# Visualize prize distribution with ASCII charts
python manage.py visualize_distribution CONTEST_CODE

# Run distribution simulation
python test_prize_distribution.py CONTEST_CODE
``` 