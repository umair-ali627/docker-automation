#!/bin/bash
set -e

echo "[$(date)] Starting initialization process..."

# Create symbolic link from /code/.env to /code/src/.env
echo "[$(date)] Setting up environment file..."
if [ -f /code/.env ]; then
  echo "[$(date)] Found .env file at /code/.env"
  mkdir -p /code/src
  ln -sf /code/.env /code/src/.env
  echo "[$(date)] Created symbolic link to /code/src/.env"
  ls -la /code/src/.env
else
  echo "[$(date)] Warning: .env file not found at /code/.env"
fi

# Wait for the database to be ready
echo "[$(date)] Waiting for database to be ready..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "[$(date)] Database is ready!"

# Set Python path and working directory
cd /code/src
export PYTHONPATH=/code/src:$PYTHONPATH

# Run migrations
echo "[$(date)] Running migrations..."
alembic upgrade head

# Start the application
echo "[$(date)] Starting the application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload