#!/bin/bash
# =============================================================================
# ZCHPC ERP - Local Development Runner (Bash)
# =============================================================================
# Run the entire system locally using Docker for debugging
# =============================================================================

set -e

echo "=========================================="
echo "ZCHPC ERP - Local Development"
echo "=========================================="

# Change to script directory
cd "$(dirname "$0")"

# Parse arguments
ACTION="start"
SERVICE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            ACTION="build"
            shift
            ;;
        --down|-d)
            ACTION="down"
            shift
            ;;
        --logs|-l)
            ACTION="logs"
            shift
            ;;
        --clean|-c)
            ACTION="clean"
            shift
            ;;
        --service|-s)
            SERVICE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./run-local.sh [--build|--down|--logs|--clean] [--service <name>]"
            exit 1
            ;;
    esac
done

case $ACTION in
    clean)
        echo -e "\n[CLEAN] Stopping and removing all containers, volumes, and images..."
        docker compose -f docker-compose.local.yml down -v --rmi local
        echo "[CLEAN] Done!"
        ;;
    down)
        echo -e "\n[DOWN] Stopping all containers..."
        docker compose -f docker-compose.local.yml down
        echo "[DOWN] Done!"
        ;;
    logs)
        if [ -n "$SERVICE" ]; then
            echo -e "\n[LOGS] Showing logs for $SERVICE..."
            docker compose -f docker-compose.local.yml logs -f "$SERVICE"
        else
            echo -e "\n[LOGS] Showing logs for all services..."
            docker compose -f docker-compose.local.yml logs -f
        fi
        ;;
    build)
        echo -e "\n[BUILD] Building images (this may take a while)..."
        docker compose -f docker-compose.local.yml build --no-cache
        echo -e "\n[START] Starting all services..."
        docker compose -f docker-compose.local.yml up -d
        ;;
    start)
        echo -e "\n[INFO] Starting ZCHPC ERP locally..."
        echo "[START] Building and starting all services..."
        docker compose -f docker-compose.local.yml up --build -d
        ;;
esac

if [ "$ACTION" = "start" ] || [ "$ACTION" = "build" ]; then
    echo -e "\n[INFO] Waiting for services to be healthy..."
    sleep 10

    # Check service status
    echo -e "\n[STATUS] Service Status:"
    docker compose -f docker-compose.local.yml ps

    echo ""
    echo "=========================================="
    echo "LOCAL DEVELOPMENT URLS"
    echo "=========================================="
    echo "Main ERP Frontend:  http://localhost:3000"
    echo "Employee Portal:    http://localhost:3001"
    echo "API:                http://localhost:8000"
    echo "API Health:         http://localhost:8000/api/v2/health/"
    echo "Admin:              http://localhost:8000/admin/"
    echo "=========================================="
    echo ""
    echo "Default Admin Credentials:"
    echo "  Email:    admin@local.dev"
    echo "  Password: admin123"
    echo "=========================================="
    echo ""
    echo "Useful Commands:"
    echo "  ./run-local.sh --logs              # View all logs"
    echo "  ./run-local.sh --logs --service api # View API logs"
    echo "  ./run-local.sh --down              # Stop all services"
    echo "  ./run-local.sh --clean             # Remove everything"
    echo "  ./run-local.sh --build             # Rebuild and start"
    echo "=========================================="

    # Show API logs to see startup progress
    echo -e "\n[LOGS] Following API logs (Ctrl+C to exit)..."
    docker compose -f docker-compose.local.yml logs -f api
fi
