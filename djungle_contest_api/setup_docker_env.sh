#!/bin/bash
# Script to set up Docker environment directories for Djungle Contest API

# Create nginx config directory
mkdir -p nginx/conf.d

# Create static and media volume directories
mkdir -p static media

# Create logs directory if it doesn't exist
mkdir -p logs

# Make entrypoint scripts executable
chmod +x entrypoint.sh
chmod +x entrypoint.prod.sh

# Create .env.prod file from example if it doesn't exist
if [ ! -f .env.prod ]; then
    echo "Creating .env.prod from example template..."
    cp .env.prod.example .env.prod
    echo "Please update .env.prod with your production settings."
fi

echo "Docker environment directories created successfully!"
echo "You can now run Docker Compose:"
echo "  - For development: docker-compose up --build"
echo "  - For production: docker-compose -f docker-compose.prod.yml up --build" 