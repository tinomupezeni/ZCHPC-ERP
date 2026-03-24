# =============================================================================
# ZCHPC ERP - Build and Push Docker Images to Docker Hub (PowerShell)
# =============================================================================
# Usage:
#   .\build-and-push.ps1                    # Build and push all images with 'latest' tag
#   .\build-and-push.ps1 -Version v1.0.0    # Build and push all images with specific version
#   .\build-and-push.ps1 -Version v1.0.0 -Target api  # Build and push only the api image
# =============================================================================

param(
    [string]$Version = "latest",
    [ValidateSet("all", "api", "frontend", "portal")]
    [string]$Target = "all"
)

# Configuration
$DOCKER_HUB_USER = "tinotenda762"
$PROJECT_NAME = "zchpc-erp"

# Image names
$API_IMAGE = "${DOCKER_HUB_USER}/${PROJECT_NAME}-api"
$FRONTEND_IMAGE = "${DOCKER_HUB_USER}/${PROJECT_NAME}-frontend"
$PORTAL_IMAGE = "${DOCKER_HUB_USER}/${PROJECT_NAME}-portal"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------
function Write-Info { param($Message) Write-Host "[INFO] $Message" -ForegroundColor Blue }
function Write-Success { param($Message) Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param($Message) Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error { param($Message) Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Print-Banner {
    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  ZCHPC ERP - Docker Build & Push" -ForegroundColor Cyan
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host "  Docker Hub: $DOCKER_HUB_USER" -ForegroundColor White
    Write-Host "  Version:    $Version" -ForegroundColor White
    Write-Host "  Target:     $Target" -ForegroundColor White
    Write-Host "==============================================" -ForegroundColor Cyan
    Write-Host ""
}

# -----------------------------------------------------------------------------
# Check Prerequisites
# -----------------------------------------------------------------------------
function Check-Prerequisites {
    Write-Info "Checking prerequisites..."

    # Check if Docker is installed
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }

    # Check if Docker is running
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Docker is not running. Please start Docker Desktop."
        exit 1
    }

    Write-Success "Prerequisites check passed"
}

# -----------------------------------------------------------------------------
# Build Functions
# -----------------------------------------------------------------------------
function Build-Api {
    Write-Info "Building API image: ${API_IMAGE}:${Version}"

    docker build `
        -t "${API_IMAGE}:${Version}" `
        -t "${API_IMAGE}:latest" `
        -f ./erp_project/Dockerfile `
        ./erp_project

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build API image"
        exit 1
    }

    Write-Success "API image built successfully"
}

function Build-Frontend {
    Write-Info "Building Frontend image: ${FRONTEND_IMAGE}:${Version}"

    # Production API URL for main ERP frontend
    $apiUrl = if ($env:VITE_API_URL) { $env:VITE_API_URL } else { "https://zchpcerp.zchpc.ac.zw" }

    docker build `
        -t "${FRONTEND_IMAGE}:${Version}" `
        -t "${FRONTEND_IMAGE}:latest" `
        --build-arg "VITE_API_URL=${apiUrl}" `
        -f ./zchpc-erp-synergy-main/Dockerfile `
        ./zchpc-erp-synergy-main

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Frontend image"
        exit 1
    }

    Write-Success "Frontend image built successfully (API: ${apiUrl})"
}

function Build-Portal {
    Write-Info "Building Portal image: ${PORTAL_IMAGE}:${Version}"

    # Production API URL for employee portal
    $apiUrl = if ($env:VITE_API_URL) { $env:VITE_API_URL } else { "https://employees.zchpc.ac.zw" }

    docker build `
        -t "${PORTAL_IMAGE}:${Version}" `
        -t "${PORTAL_IMAGE}:latest" `
        --build-arg "VITE_API_URL=${apiUrl}" `
        -f ./employee-portal/Dockerfile `
        ./employee-portal

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to build Portal image"
        exit 1
    }

    Write-Success "Portal image built successfully (API: ${apiUrl})"
}

# -----------------------------------------------------------------------------
# Push Functions
# -----------------------------------------------------------------------------
function Push-Api {
    Write-Info "Pushing API image to Docker Hub..."

    docker push "${API_IMAGE}:${Version}"
    if ($Version -ne "latest") {
        docker push "${API_IMAGE}:latest"
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push API image"
        exit 1
    }

    Write-Success "API image pushed: ${API_IMAGE}:${Version}"
}

function Push-Frontend {
    Write-Info "Pushing Frontend image to Docker Hub..."

    docker push "${FRONTEND_IMAGE}:${Version}"
    if ($Version -ne "latest") {
        docker push "${FRONTEND_IMAGE}:latest"
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push Frontend image"
        exit 1
    }

    Write-Success "Frontend image pushed: ${FRONTEND_IMAGE}:${Version}"
}

function Push-Portal {
    Write-Info "Pushing Portal image to Docker Hub..."

    docker push "${PORTAL_IMAGE}:${Version}"
    if ($Version -ne "latest") {
        docker push "${PORTAL_IMAGE}:latest"
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to push Portal image"
        exit 1
    }

    Write-Success "Portal image pushed: ${PORTAL_IMAGE}:${Version}"
}

# -----------------------------------------------------------------------------
# Main Execution
# -----------------------------------------------------------------------------
function Main {
    Print-Banner
    Check-Prerequisites

    # Ensure we're in the project root
    $scriptDir = Split-Path -Parent $MyInvocation.ScriptName
    Set-Location $scriptDir

    switch ($Target) {
        "api" {
            Build-Api
            Push-Api
        }
        "frontend" {
            Build-Frontend
            Push-Frontend
        }
        "portal" {
            Build-Portal
            Push-Portal
        }
        "all" {
            Build-Api
            Build-Frontend
            Build-Portal

            Write-Host ""
            Write-Info "All images built. Starting push to Docker Hub..."
            Write-Host ""

            Push-Api
            Push-Frontend
            Push-Portal
        }
    }

    Write-Host ""
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host "  Build & Push Complete!" -ForegroundColor Green
    Write-Host "==============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Images pushed to Docker Hub:" -ForegroundColor White
    Write-Host "  - ${API_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host "  - ${FRONTEND_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host "  - ${PORTAL_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host ""
    Write-Host "To pull these images:" -ForegroundColor White
    Write-Host "  docker pull ${API_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host "  docker pull ${FRONTEND_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host "  docker pull ${PORTAL_IMAGE}:${Version}" -ForegroundColor Gray
    Write-Host ""
}

# Run main function
Main
