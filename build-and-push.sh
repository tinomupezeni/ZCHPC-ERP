#!/bin/bash
# =============================================================================
# ZCHPC ERP - Build and Push Docker Images to Docker Hub
# =============================================================================
# Usage:
#   ./build-and-push.sh              # Build and push all images with 'latest' tag
#   ./build-and-push.sh v1.0.0       # Build and push all images with specific version
#   ./build-and-push.sh v1.0.0 api   # Build and push only the api image
# =============================================================================

set -e

# Configuration
DOCKER_HUB_USER="tinotenda762"
PROJECT_NAME="zchpc-erp"

# Image names
API_IMAGE="${DOCKER_HUB_USER}/${PROJECT_NAME}-api"
FRONTEND_IMAGE="${DOCKER_HUB_USER}/${PROJECT_NAME}-frontend"
PORTAL_IMAGE="${DOCKER_HUB_USER}/${PROJECT_NAME}-portal"

# Version tag (default: latest)
VERSION="${1:-latest}"
TARGET="${2:-all}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_banner() {
    echo ""
    echo "=============================================="
    echo "  ZCHPC ERP - Docker Build & Push"
    echo "=============================================="
    echo "  Docker Hub: ${DOCKER_HUB_USER}"
    echo "  Version:    ${VERSION}"
    echo "  Target:     ${TARGET}"
    echo "=============================================="
    echo ""
}

# -----------------------------------------------------------------------------
# Check Prerequisites
# -----------------------------------------------------------------------------
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi

    # Check if logged in to Docker Hub
    if ! docker info 2>/dev/null | grep -q "Username"; then
        log_warning "Not logged in to Docker Hub. Attempting login..."
        docker login
    fi

    log_success "Prerequisites check passed"
}

# -----------------------------------------------------------------------------
# Build Functions
# -----------------------------------------------------------------------------
build_api() {
    log_info "Building API image: ${API_IMAGE}:${VERSION}"

    docker build \
        -t "${API_IMAGE}:${VERSION}" \
        -t "${API_IMAGE}:latest" \
        -f ./erp_project/Dockerfile \
        ./erp_project

    log_success "API image built successfully"
}

build_frontend() {
    log_info "Building Frontend image: ${FRONTEND_IMAGE}:${VERSION}"

    # Production API URL for main ERP frontend
    local api_url="${VITE_API_URL:-https://zchpcerp.zchpc.ac.zw}"

    docker build \
        -t "${FRONTEND_IMAGE}:${VERSION}" \
        -t "${FRONTEND_IMAGE}:latest" \
        --build-arg VITE_API_URL="${api_url}" \
        -f ./zchpc-erp-synergy-main/Dockerfile \
        ./zchpc-erp-synergy-main

    log_success "Frontend image built successfully (API: ${api_url})"
}

build_portal() {
    log_info "Building Portal image: ${PORTAL_IMAGE}:${VERSION}"

    # Production API URL for employee portal
    local api_url="${VITE_API_URL:-https://employees.zchpc.ac.zw}"

    docker build \
        -t "${PORTAL_IMAGE}:${VERSION}" \
        -t "${PORTAL_IMAGE}:latest" \
        --build-arg VITE_API_URL="${api_url}" \
        -f ./employee-portal/Dockerfile \
        ./employee-portal

    log_success "Portal image built successfully (API: ${api_url})"
}

# -----------------------------------------------------------------------------
# Push Functions
# -----------------------------------------------------------------------------
push_api() {
    log_info "Pushing API image to Docker Hub..."

    docker push "${API_IMAGE}:${VERSION}"
    if [ "${VERSION}" != "latest" ]; then
        docker push "${API_IMAGE}:latest"
    fi

    log_success "API image pushed: ${API_IMAGE}:${VERSION}"
}

push_frontend() {
    log_info "Pushing Frontend image to Docker Hub..."

    docker push "${FRONTEND_IMAGE}:${VERSION}"
    if [ "${VERSION}" != "latest" ]; then
        docker push "${FRONTEND_IMAGE}:latest"
    fi

    log_success "Frontend image pushed: ${FRONTEND_IMAGE}:${VERSION}"
}

push_portal() {
    log_info "Pushing Portal image to Docker Hub..."

    docker push "${PORTAL_IMAGE}:${VERSION}"
    if [ "${VERSION}" != "latest" ]; then
        docker push "${PORTAL_IMAGE}:latest"
    fi

    log_success "Portal image pushed: ${PORTAL_IMAGE}:${VERSION}"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
main() {
    print_banner
    check_prerequisites

    case "${TARGET}" in
        api)
            build_api
            push_api
            ;;
        frontend)
            build_frontend
            push_frontend
            ;;
        portal)
            build_portal
            push_portal
            ;;
        all)
            build_api
            build_frontend
            build_portal

            echo ""
            log_info "All images built. Starting push to Docker Hub..."
            echo ""

            push_api
            push_frontend
            push_portal
            ;;
        *)
            log_error "Unknown target: ${TARGET}"
            echo "Valid targets: all, api, frontend, portal"
            exit 1
            ;;
    esac

    echo ""
    echo "=============================================="
    echo "  Build & Push Complete!"
    echo "=============================================="
    echo ""
    echo "Images pushed to Docker Hub:"
    echo "  - ${API_IMAGE}:${VERSION}"
    echo "  - ${FRONTEND_IMAGE}:${VERSION}"
    echo "  - ${PORTAL_IMAGE}:${VERSION}"
    echo ""
    echo "To pull these images:"
    echo "  docker pull ${API_IMAGE}:${VERSION}"
    echo "  docker pull ${FRONTEND_IMAGE}:${VERSION}"
    echo "  docker pull ${PORTAL_IMAGE}:${VERSION}"
    echo ""
}

# Run main function
main
