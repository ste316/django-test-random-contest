# Docker Setup for Djungle Contest API

This document provides instructions for setting up and running the Djungle Contest API using Docker and docker-compose.

## Prerequisites

- Docker Engine (version 19.03.0+)
- Docker Compose (version 1.27.0+)

You can verify your installations with:
```bash
docker --version
docker-compose --version
```

## Quick Start

To start the application in development mode:

1. Clone the repository and navigate to the project directory:
```bash
cd djungle_contest_api
```

2. Build and start the containers:
```bash
docker-compose up --build
```

3. Access the API at http://localhost:8000

## Configuration

### Environment Variables

The following environment variables can be set in the docker-compose.yml file:

- `DEBUG`: Set to `True` for development mode, `False` for production
- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Django's secret key (for security in production, this should be changed)

### Volumes

The docker-compose.yml file defines several volumes:

- `static_volume`: For Django's static files
- `media_volume`: For user-uploaded media files
- `redis_data`: For persisting Redis data

## Common Commands

### Starting Services

```bash
# Start services in the foreground
docker-compose up

# Start services in the background
docker-compose up -d
```

### Stopping Services

```bash
# Stop services but preserve containers
docker-compose stop

# Stop services and remove containers
docker-compose down

# Stop services and remove containers, networks, volumes
docker-compose down -v
```

### Viewing Logs

```bash
# View logs from all services
docker-compose logs

# View logs from a specific service
docker-compose logs web

# Follow log output
docker-compose logs -f
```

### Running Commands in Containers

```bash
# Run a Python shell
docker-compose exec web python manage.py shell

# Run migrations
docker-compose exec web python manage.py migrate

# Create a superuser
docker-compose exec web python manage.py createsuperuser
```

### Running Tests

```bash
# Run all tests
docker-compose exec web python manage.py test

# Run tests for a specific app
docker-compose exec web python manage.py test contests
```

## Development Workflow

1. Make changes to the Django code
2. The changes will be automatically applied due to the volume mapping
3. If you install new dependencies, update the requirements.txt file and rebuild:
```bash
docker-compose down
docker-compose up --build
```

## Production Deployment

For production deployment, consider these additional steps:

1. Use a production-grade web server like Gunicorn instead of Django's development server
2. Set up a reverse proxy like Nginx
3. Use proper environment variables management
4. Implement healthchecks
5. Set up proper database and Redis configurations

A separate docker-compose.prod.yml file should be created for production settings.

## Troubleshooting

### Container Fails to Start

Check the logs for errors:
```bash
docker-compose logs web
```

### Database Connectivity Issues

Make sure the database service is running:
```bash
docker-compose ps
```

### Permissions Issues

If there are permission issues with volume mounts:
```bash
# Fix permissions on the logs directory
sudo chown -R $(id -u):$(id -g) ./logs
``` 