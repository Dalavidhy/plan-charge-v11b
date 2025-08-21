#!/bin/sh
set -e

echo "Starting Plan Charge backend..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
# Use environment variables with defaults
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
REDIS_HOST="${REDIS_HOST:-redis}"
REDIS_PORT="${REDIS_PORT:-6379}"

# Use pg_isready for PostgreSQL (more reliable)
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -q; do
  echo "PostgreSQL is not ready yet..."
  sleep 1
done
echo "PostgreSQL is ready!"

# Use nc for Redis (now that netcat is installed) - but don't block if Redis is unavailable
echo "Checking Redis..."
REDIS_WAIT_TIME=0
MAX_REDIS_WAIT=10
while ! nc -z "$REDIS_HOST" "$REDIS_PORT"; do
  if [ $REDIS_WAIT_TIME -ge $MAX_REDIS_WAIT ]; then
    echo "Redis is not available after ${MAX_REDIS_WAIT}s, continuing without it..."
    break
  fi
  echo "Redis is not ready yet... (${REDIS_WAIT_TIME}/${MAX_REDIS_WAIT}s)"
  sleep 1
  REDIS_WAIT_TIME=$((REDIS_WAIT_TIME + 1))
done
if [ $REDIS_WAIT_TIME -lt $MAX_REDIS_WAIT ]; then
  echo "Redis is ready!"
fi

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Seed database in development
if [ "$ENVIRONMENT" = "development" ]; then
  echo "Seeding database..."
  python -m scripts.seed_data || true
fi

# Start the application
exec "$@"
