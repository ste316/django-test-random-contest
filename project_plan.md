# Implementation Plan for Djungle Contest API

## 1. Project Overview
- The Djungle Contest API v2.4 is a Django-based application designed to handle contests where players participate in a pseudo-random prize extraction game. The system supports multiple contests running concurrently, with each contest offering a prize that can be won several times per day. Each contest is defined by a unique code, name, validity date range (inclusive), and a prize with a daily winning limit. The API endpoints allow users to participate in the contest, checking if they win a prize based on the contest configuration and pseudo-random logic ensuring an even distribution throughout the day.

## 2. Requirements & Specifications
- The Contest model will include fields such as code, name, start date, and end date. The Prize model will be linked to a contest and include fields such as prize code, name, and a daily winning limit (perday).
- The API endpoint (GET /play/) will require a contest parameter and optionally a user parameter (for bonus features). Expected responses include:
  - HTTP 400 if the contest code is missing.
  - HTTP 404 if the contest code is not found.
  - HTTP 422 if the contest is not active (outside the valid date range).
  - HTTP 200 with winning details if the pseudo-random extraction determines a win.
  - HTTP 200 with a non-winning response if the extraction does not result in a win.
- Bonus features include:
  - API Authentication for authorized access (Bonus 1).
  - Per-user daily win limits to restrict the number of wins per user (Bonus 2).

## 3. Project Structure
- The project will use a standard Django layout with separate apps for contest management. Key modules include models for data representation, views for API endpoints, utility functions for the prize extraction algorithm, and tests for both unit and integration testing. Docker configuration files will be included for environment setup.

## 4. Database Design
- A relational database (such as SQLite for development) will be used to store contest and prize information. The design includes:
  - Contest: { code, name, start_date, end_date }
  - Prize: { code, name, perday, contest (ForeignKey) }
  - Optionally, a WinRecord model to track prize winnings (globally and per user if bonus features are implemented).
- Data integrity is enforced through proper relational mappings and validations.

## 5. API Endpoint Design
- The GET /play/ endpoint will work as follows:
  - Validate that the contest parameter is provided. If missing, return HTTP 400 with an error message.
  - Check if the contest exists in the database. If not, return HTTP 404.
  - Ensure that the current date falls within the contest's active date range. If not, return HTTP 422.
  - Execute the pseudo-random win determination, ensuring the prize win count does not exceed the daily limit.
  - Return HTTP 200 with a winning response (including prize details) or a losing response with prize set to null.

## 6. Prize Distribution Mechanism
- The prize extraction algorithm is designed to ensure that the total daily wins equal the prize's daily limit. This is achieved through a pseudo-random mechanism that factors in the timing of requests to evenly distribute wins over a 24-hour period.

## 7. Docker & docker-compose Configuration
- A Dockerfile will be created to containerize the Django application.
- A docker-compose.yml file will be provided to set up and run the Django application alongside the relational database service.
- The documentation will include instructions for initializing and running the project in a local environment using Docker.

## 8. Testing Strategy
- Comprehensive unit tests will be implemented for functions including validation, random win calculation, and database interactions.
- Integration tests will cover the API endpoints and ensure correct end-to-end behavior.
- A Continuous Integration (CI) pipeline may be set up to run tests automatically.
- The testing strategy will focus on achieving high coverage and ensuring robustness of the pseudo-random algorithm.

## 9. Code Quality and Logging Requirements
- **Code Quality:**
  - Code will follow best practices for modularity and readability, with each function designed to perform a single task.
  - Each function will include detailed docstrings describing inputs, outputs, and expected behavior.
  - Debug mode will be available with enhanced logging for deep troubleshooting during development and production diagnosis.
- **Logging:**
  - Every request to the API will be logged with details such as timestamp, endpoint, parameters, and outcome.
  - Key actions such as contest validation, win/loss evaluation, prize distribution updates, and error conditions will be logged at appropriate levels (DEBUG, INFO, ERROR).

## 10. Bonus Features (Optional)
- **Bonus 1: API Authentication**
  - The system may implement token-based authentication to restrict API access to authorized clients.
  - Unauthorized requests will return HTTP 401, while authenticated users lacking permissions for a contest will receive HTTP 403.
- **Bonus 2: Per-user Daily Win Limits**
  - The API can be extended to accept a 'user' parameter in GET /play/?contest={code}&user={user_id}.
  - A limit (WMAX) will be enforced to restrict the number of wins per user per day.
  - If the user exceeds the limit, HTTP 420 will be returned with an appropriate message.

## 11. Timeline and Milestones
- **Step-by-step phases:**
  1. Requirements analysis and design approval.
  2. Setting up the Django project and defining models.
  3. Implementing the core /play/ endpoint.
  4. Designing and implementing the prize distribution logic.
  5. Integrating logging and debugging facilities.
  6. Docker and docker-compose configuration.
  7. Unit and integration testing.
  8. Optional bonus features implementation.
- Estimated time allocation and overall milestones will be defined during the planning phase.

## 12. Documentation
- In-code documentation will follow standard Python docstring conventions.
- A README file will detail project setup, API usage, and design decisions effective for developers and users.
- Additional documentation will cover deployment procedures and guidelines to run tests. 