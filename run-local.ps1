# =============================================================================
# ZCHPC ERP - Local Development Runner (PowerShell)
# =============================================================================
# Run the entire system locally using Docker for debugging
# =============================================================================

param(
    [switch]$Build,
    [switch]$Down,
    [switch]$Logs,
    [switch]$Clean,
    [string]$Service
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "ZCHPC ERP - Local Development"
Write-Host "=========================================="

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

if ($Clean) {
    Write-Host "`n[CLEAN] Stopping and removing all containers, volumes, and images..."
    docker compose -f docker-compose.local.yml down -v --rmi local
    Write-Host "[CLEAN] Done!"
    exit 0
}

if ($Down) {
    Write-Host "`n[DOWN] Stopping all containers..."
    docker compose -f docker-compose.local.yml down
    Write-Host "[DOWN] Done!"
    exit 0
}

if ($Logs) {
    if ($Service) {
        Write-Host "`n[LOGS] Showing logs for $Service..."
        docker compose -f docker-compose.local.yml logs -f $Service
    } else {
        Write-Host "`n[LOGS] Showing logs for all services..."
        docker compose -f docker-compose.local.yml logs -f
    }
    exit 0
}

# Default: Start the system
Write-Host "`n[INFO] Starting ZCHPC ERP locally..."

if ($Build) {
    Write-Host "[BUILD] Building images (this may take a while)..."
    docker compose -f docker-compose.local.yml build --no-cache
}

Write-Host "[START] Starting all services..."
docker compose -f docker-compose.local.yml up --build -d

Write-Host "`n[INFO] Waiting for services to be healthy..."
Start-Sleep -Seconds 10

# Check service status
Write-Host "`n[STATUS] Service Status:"
docker compose -f docker-compose.local.yml ps

Write-Host "`n=========================================="
Write-Host "LOCAL DEVELOPMENT URLS"
Write-Host "=========================================="
Write-Host "Main ERP Frontend:  http://localhost:3000"
Write-Host "Employee Portal:    http://localhost:3001"
Write-Host "API:                http://localhost:8000"
Write-Host "API Health:         http://localhost:8000/api/v2/health/"
Write-Host "Admin:              http://localhost:8000/admin/"
Write-Host "=========================================="
Write-Host ""
Write-Host "Default Admin Credentials:"
Write-Host "  Email:    admin@local.dev"
Write-Host "  Password: admin123"
Write-Host "=========================================="
Write-Host ""
Write-Host "Useful Commands:"
Write-Host "  .\run-local.ps1 -Logs           # View all logs"
Write-Host "  .\run-local.ps1 -Logs -Service api  # View API logs"
Write-Host "  .\run-local.ps1 -Down           # Stop all services"
Write-Host "  .\run-local.ps1 -Clean          # Remove everything"
Write-Host "  .\run-local.ps1 -Build          # Rebuild and start"
Write-Host "=========================================="

# Show API logs to see startup progress
Write-Host "`n[LOGS] Following API logs (Ctrl+C to exit)..."
docker compose -f docker-compose.local.yml logs -f api
