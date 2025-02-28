# Phase 2: Setting up the Django Project and Defining Models

## Overview
In Phase 2, we successfully set up the Django project for the Djungle Contest API, focusing on creating a robust data model that supports the contest and prize distribution requirements.

## Key Accomplishments

### 1. Project Structure
- Created a new Django project `djungle_contest_api`
- Developed a dedicated `contests` app for core functionality
- Configured project settings and dependencies
- Set up virtual environment and dependency management

### 2. Database Model Design
#### Contest Model
- Implemented `Contest` model with key attributes:
  - `code`: Unique identifier
  - `name`: Contest name
  - `start_date`: Contest start date
  - `end_date`: Contest end date
- Added `is_active()` method to check contest validity

#### Prize Model
- Created `Prize` model with essential fields:
  - `code`: Unique prize identifier
  - `name`: Prize name
  - `perday`: Maximum daily wins
  - `contest`: Foreign key relationship to Contest
- Implemented methods:
  - `get_wins_today()`: Tracks daily wins
  - `can_win_today()`: Checks daily win limit

#### WinRecord Model
- Developed `WinRecord` model for tracking prize wins:
  - `prize`: Foreign key to Prize
  - `user_id`: Optional user identifier
  - `timestamp`: Win record creation time

### 3. Admin Interface Configuration
- Registered models in Django admin
- Created custom admin classes with:
  - List displays
  - Search fields
  - Filtering capabilities

### 4. Database Migrations
- Generated initial database migrations
- Applied migrations to create database schema
- Created SQLite database for development

### 5. Utility Functions
- Implemented `utils.py` with key functions:
  - `determine_win()`: Pseudo-random win determination
  - `get_win_distribution_stats()`: Win distribution analysis

### 6. Project Documentation
- Updated `README.md` with:
  - Project overview
  - Setup instructions
  - API endpoint descriptions
- Created comprehensive docstrings for models and utility functions

## Technical Details
- **Framework**: Django 5.1.6
- **Database**: SQLite
- **Python Version**: 3.8+
- **Key Libraries**: 
  - Django ORM
  - Django Admin
  - Random and datetime modules

## Challenges Addressed
- Designing a flexible contest and prize model
- Implementing an even win distribution mechanism
- Ensuring data integrity and relationships
- Providing comprehensive model documentation

## Design Principles
- Modularity: Each model and function has a single, well-defined responsibility
- Extensibility: Models support future bonus features
- Readability: Clear, descriptive naming and docstrings
- Flexibility: Support for multiple concurrent contests

## Next Steps
- Implement the core `/play/` endpoint
- Develop prize distribution logic
- Create comprehensive test suite
- Consider performance optimizations

## Conclusion
Phase 2 successfully established a solid foundation for the Djungle Contest API, creating a robust and flexible data model that supports the project's complex prize distribution requirements. 