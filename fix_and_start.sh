#!/bin/bash

# Stop any existing container
docker rm -f smartvoice-web-1 || true

# Run the container with environment variables and sleep command to keep it running
docker run -d --name smartvoice-web-1 \
  --network=smartvoice_default \
  -p 8000:8000 \
  -e PYTHONPATH=/code/src \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=postgres \
  -e POSTGRES_SERVER=db \
  -e POSTGRES_PORT=5432 \
  -e POSTGRES_URI="postgres:postgres@db:5432/postgres" \
  -e POSTGRES_URL="postgresql+asyncpg://postgres:postgres@db:5432/postgres" \
  -e REDIS_HOST=redis \
  -e REDIS_PORT=6379 \
  -e SECRET_KEY="supersecretkey" \
  ghcr.io/humayun-nisar/smartvoice/smartvoice:latest \
  sleep infinity

# Create the .env file inside the container
docker exec -it smartvoice-web-1 bash -c 'cat > /code/.env << EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_URI=postgres:postgres@db:5432/postgres
POSTGRES_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres
REDIS_HOST=redis
REDIS_PORT=6379
SECRET_KEY=supersecretkey
EOF
chmod 644 /code/.env
cat /code/.env'

# Run the migrations
docker exec -it smartvoice-web-1 bash -c 'cd /code/src && PYTHONPATH=/code/src alembic upgrade head'

# Start the application
docker exec -it smartvoice-web-1 bash -c 'cd /code/src && PYTHONPATH=/code/src exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload' 