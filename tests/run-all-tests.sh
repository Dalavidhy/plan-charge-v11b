#!/bin/bash

# Run all tests for Plan Charge v11b
# Usage: ./run-all-tests.sh

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Test results
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

echo -e "${MAGENTA}╔════════════════════════════════════════╗${NC}"
echo -e "${MAGENTA}║     Plan Charge v11b Test Suite       ║${NC}"
echo -e "${MAGENTA}╚════════════════════════════════════════╝${NC}"
echo ""

# Function to run a test
run_test() {
    local test_name=$1
    local test_script=$2
    
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}🧪 Running: $test_name${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -f "$test_script" ]; then
        # Make script executable
        chmod +x "$test_script"
        
        # Run the test
        if $test_script; then
            echo -e "\n✅ ${GREEN}$test_name: PASSED${NC}"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "\n❌ ${RED}$test_name: FAILED${NC}"
            TESTS_FAILED=$((TESTS_FAILED + 1))
            FAILED_TESTS+=("$test_name")
        fi
    else
        echo -e "⚠️  ${YELLOW}$test_name: SKIPPED (script not found)${NC}"
        echo "Missing: $test_script"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "❌ ${RED}Docker is not installed${NC}"
        exit 1
    fi
    echo -e "✅ Docker is installed"
    
    # Check Docker Compose
    if ! command -v docker &> /dev/null; then
        echo -e "❌ ${RED}Docker Compose is not installed${NC}"
        exit 1
    fi
    echo -e "✅ Docker Compose is installed"
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        echo -e "⚠️  ${YELLOW}jq is not installed (some tests may fail)${NC}"
        echo "Install with: brew install jq (macOS) or apt-get install jq (Linux)"
    else
        echo -e "✅ jq is installed"
    fi
    
    # Check curl
    if ! command -v curl &> /dev/null; then
        echo -e "❌ ${RED}curl is not installed${NC}"
        exit 1
    fi
    echo -e "✅ curl is installed"
    
    echo ""
}

# Function to setup environment
setup_environment() {
    echo -e "${BLUE}🔧 Setting up environment...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Create .env if it doesn't exist
    if [ ! -f .env ]; then
        echo "Creating .env file from example..."
        cp .env.example .env
    fi
    
    # Ensure test scripts are executable
    find tests -name "*.sh" -type f -exec chmod +x {} \;
    
    echo -e "✅ Environment ready"
    echo ""
}

# Function to start services
start_services() {
    echo -e "${BLUE}🚀 Starting Docker services...${NC}"
    
    # Stop any existing containers
    docker compose down 2>/dev/null || true
    
    # Start services
    docker compose up -d --build
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    if [ -f "$SCRIPT_DIR/docker/wait-for-healthy.sh" ]; then
        chmod +x "$SCRIPT_DIR/docker/wait-for-healthy.sh"
        "$SCRIPT_DIR/docker/wait-for-healthy.sh" 120
    else
        echo "Wait script not found, sleeping 30 seconds..."
        sleep 30
    fi
    
    echo -e "✅ Services are running"
    echo ""
}

# Function to show test results
show_results() {
    echo -e "\n${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}📊 TEST RESULTS${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    TOTAL_TESTS=$((TESTS_PASSED + TESTS_FAILED))
    
    echo -e "Total Tests: $TOTAL_TESTS"
    echo -e "✅ Passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "❌ Failed: ${RED}$TESTS_FAILED${NC}"
    
    if [ ${#FAILED_TESTS[@]} -gt 0 ]; then
        echo -e "\n${RED}Failed Tests:${NC}"
        for test in "${FAILED_TESTS[@]}"; do
            echo -e "  • $test"
        done
    fi
    
    # Calculate pass rate
    if [ $TOTAL_TESTS -gt 0 ]; then
        PASS_RATE=$(echo "scale=1; $TESTS_PASSED * 100 / $TOTAL_TESTS" | bc)
        echo -e "\nPass Rate: ${PASS_RATE}%"
        
        if [ "$TESTS_FAILED" -eq 0 ]; then
            echo -e "\n🎉 ${GREEN}All tests passed!${NC} 🎉"
        fi
    fi
}

# Function to cleanup
cleanup() {
    echo -e "\n${BLUE}🧹 Cleaning up...${NC}"
    
    if [ "${KEEP_RUNNING:-false}" != "true" ]; then
        docker compose down
        echo -e "✅ Services stopped"
    else
        echo -e "ℹ️  Services kept running (KEEP_RUNNING=true)"
        echo -e "Stop with: docker compose down"
    fi
}

# Main execution
main() {
    # Trap errors and cleanup
    trap cleanup EXIT
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --keep-running)
                export KEEP_RUNNING=true
                ;;
            --skip-build)
                export SKIP_BUILD=true
                ;;
            --help)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --keep-running  Keep services running after tests"
                echo "  --skip-build    Skip Docker build step"
                echo "  --help          Show this help message"
                exit 0
                ;;
        esac
        shift
    done
    
    # Run prerequisites check
    check_prerequisites
    
    # Setup environment
    setup_environment
    
    # Start services if not skipping build
    if [ "${SKIP_BUILD:-false}" != "true" ]; then
        start_services
    else
        echo -e "${YELLOW}Skipping build step (--skip-build)${NC}\n"
    fi
    
    # Run tests
    echo -e "${MAGENTA}🚀 Starting Test Suite${NC}"
    
    # 1. Docker health tests
    run_test "Docker Health Check" "$SCRIPT_DIR/docker/wait-for-healthy.sh"
    
    # 2. Authentication tests
    run_test "Authentication Flow" "$SCRIPT_DIR/auth/test-auth-flow.sh"
    
    # 3. Frontend tests
    run_test "Frontend Pages" "$SCRIPT_DIR/frontend/test-pages.sh"
    
    # 4. API tests (if exists)
    if [ -f "$SCRIPT_DIR/api/test-endpoints.sh" ]; then
        run_test "API Endpoints" "$SCRIPT_DIR/api/test-endpoints.sh"
    fi
    
    # 5. E2E tests (if exists)
    if [ -f "$SCRIPT_DIR/e2e/user-journey.sh" ]; then
        run_test "E2E User Journey" "$SCRIPT_DIR/e2e/user-journey.sh"
    fi
    
    # Show results
    show_results
    
    # Exit with appropriate code
    if [ $TESTS_FAILED -gt 0 ]; then
        exit 1
    else
        exit 0
    fi
}

# Run main function
main "$@"