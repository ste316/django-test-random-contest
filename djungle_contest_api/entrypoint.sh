#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create necessary log directories if they don't exist
mkdir -p logs

# Start Django development server
echo "Starting Django server..."
exec python manage.py runserver 0.0.0.0:8000 