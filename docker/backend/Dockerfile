# Multi-stage Dockerfile for Plan Charge backend

# Base stage with Python and system dependencies
FROM python:3.11-slim AS base

# Install system dependencies including C++ compiler for numpy and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    curl \
    make \
    cmake \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies stage
FROM base AS dependencies

# Copy requirements files
COPY backend/requirements*.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Development stage
FROM dependencies AS development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY backend/ .

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Testing stage
FROM development AS testing

# Run tests by default
CMD ["pytest", "-v", "--cov=app", "--cov-report=term-missing"]

# Production stage
FROM dependencies AS production

# Copy only necessary application code
COPY backend/app ./app
COPY backend/migrations ./migrations

# Create non-root user
RUN addgroup -g 1000 -S appuser && \
    adduser -u 1000 -S appuser -G appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command with gunicorn
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
