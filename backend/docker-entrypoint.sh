#!/bin/sh
set -e

echo "Starting Plan Charge backend..."

# Wait for database to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

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