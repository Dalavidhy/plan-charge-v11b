#!/bin/bash

# Wait for all Docker services to be healthy
# Usage: ./wait-for-healthy.sh [timeout_seconds]

set -e

TIMEOUT=${1:-300}  # Default 5 minutes
INTERVAL=5
ELAPSED=0

echo "⏳ Waiting for services to be healthy (timeout: ${TIMEOUT}s)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service_health() {
    local service=$1
    local status=$(docker compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .Health")

    if [ -z "$status" ]; then
        status=$(docker compose ps --format json | jq -r ".[] | select(.Service == \"$service\") | .State")
    fi

    echo "$status"
}

# Services to check
SERVICES=("postgres" "redis" "backend" "frontend")

while [ $ELAPSED -lt $TIMEOUT ]; do
    ALL_HEALTHY=true

    echo -e "\n📊 Service Status (${ELAPSED}s elapsed):"
    echo "================================"

    for service in "${SERVICES[@]}"; do
        status=$(check_service_health "$service")

        case "$status" in
            "healthy"|"running")
                echo -e "✅ ${GREEN}$service${NC}: $status"
                ;;
            "starting"|"unhealthy")
                echo -e "⏳ ${YELLOW}$service${NC}: $status"
                ALL_HEALTHY=false
                ;;
            *)
                echo -e "❌ ${RED}$service${NC}: $status"
                ALL_HEALTHY=false
                ;;
        esac
    done

    if [ "$ALL_HEALTHY" = true ]; then
        echo -e "\n🎉 ${GREEN}All services are healthy!${NC}"

        # Additional checks
        echo -e "\n🔍 Running additional health checks..."

        # Check backend API
        if curl -f -s http://localhost:8000/health > /dev/null; then
            echo -e "✅ Backend API is responding"
        else
            echo -e "❌ ${RED}Backend API is not responding${NC}"
            ALL_HEALTHY=false
        fi

        # Check frontend
        if curl -f -s http://localhost:5173 > /dev/null 2>&1; then
            echo -e "✅ Frontend is responding"
        else
            echo -e "⚠️  ${YELLOW}Frontend might still be building...${NC}"
        fi

        # Check database connection
        if docker compose exec -T postgres pg_isready -U plancharge > /dev/null 2>&1; then
            echo -e "✅ PostgreSQL is accepting connections"
        else
            echo -e "❌ ${RED}PostgreSQL is not accepting connections${NC}"
            ALL_HEALTHY=false
        fi

        # Check Redis connection
        if docker compose exec -T redis redis-cli ping > /dev/null 2>&1; then
            echo -e "✅ Redis is responding"
        else
            echo -e "❌ ${RED}Redis is not responding${NC}"
            ALL_HEALTHY=false
        fi

        if [ "$ALL_HEALTHY" = true ]; then
            echo -e "\n✨ ${GREEN}All health checks passed!${NC}"
            exit 0
        fi
    fi

    echo -e "\n⏳ Waiting ${INTERVAL} seconds before next check..."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo -e "\n❌ ${RED}Timeout waiting for services to be healthy${NC}"
echo -e "\n📋 Docker Compose logs:"
docker compose logs --tail=50
exit 1
