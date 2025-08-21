#!/bin/bash

# Plan Charge - Docker Startup Script
# =====================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENV_MODE="development"
COMPOSE_FILE="docker-compose.yml"
BUILD_FLAG=""
DETACHED=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|--production)
            ENV_MODE="production"
            COMPOSE_FILE="docker-compose.prod.yml"
            shift
            ;;
        --build)
            BUILD_FLAG="--build"
            shift
            ;;
        --detached|-d)
            DETACHED="-d"
            shift
            ;;
        --help|-h)
            echo "Usage: ./start.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod, --production  Start in production mode"
            echo "  --build              Rebuild Docker images"
            echo "  -d, --detached       Run in detached mode"
            echo "  -h, --help           Show this help message"
            echo ""
            echo "Examples:"
            echo "  ./start.sh                    # Start in development mode"
            echo "  ./start.sh --prod             # Start in production mode"
            echo "  ./start.sh --build -d         # Rebuild and run detached"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}    Plan Charge - Resource Planning    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check for .env file
if [ "$ENV_MODE" = "development" ]; then
    if [ ! -f .env ]; then
        echo -e "${YELLOW}Warning: .env file not found${NC}"
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}Created .env file. Please update it with your configuration.${NC}"
    fi
else
    if [ ! -f .env.production ]; then
        echo -e "${RED}Error: .env.production file not found for production mode${NC}"
        echo "Please create .env.production with production configuration"
        exit 1
    fi
fi

# Display startup information
echo -e "Mode: ${YELLOW}$ENV_MODE${NC}"
echo -e "Compose file: ${YELLOW}$COMPOSE_FILE${NC}"
echo ""

# Stop any existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker compose -f $COMPOSE_FILE down 2>/dev/null || true

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker compose -f $COMPOSE_FILE up $BUILD_FLAG $DETACHED

if [ "$DETACHED" = "-d" ]; then
    echo ""
    echo -e "${GREEN}Services started successfully!${NC}"
    echo ""
    echo "Access points:"
    echo -e "  Frontend:  ${GREEN}http://localhost:3000${NC}"
    echo -e "  Backend:   ${GREEN}http://localhost:8000${NC}"
    echo -e "  API Docs:  ${GREEN}http://localhost:8000/docs${NC}"
    echo ""
    echo "Database:"
    echo -e "  PostgreSQL: ${GREEN}localhost:5432${NC}"
    echo -e "  Redis:      ${GREEN}localhost:6379${NC}"
    echo ""
    echo "Logs:"
    echo -e "  View all:     ${YELLOW}docker compose -f $COMPOSE_FILE logs -f${NC}"
    echo -e "  View backend: ${YELLOW}docker compose -f $COMPOSE_FILE logs -f backend${NC}"
    echo -e "  View frontend:${YELLOW}docker compose -f $COMPOSE_FILE logs -f frontend${NC}"
    echo ""
    echo "Stop services:"
    echo -e "  ${YELLOW}docker compose -f $COMPOSE_FILE down${NC}"
fi
