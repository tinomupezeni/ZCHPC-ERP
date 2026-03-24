#!/bin/bash
# =============================================================================
# ZCHPC ERP - Docker Entrypoint Script
# =============================================================================
# This script runs when the container starts and handles:
# - Database connection waiting
# - Database migrations
# - Static file collection
# - Starting the application server
# =============================================================================

set -e

echo "=========================================="
echo "ZCHPC ERP - Starting Application"
echo "=========================================="

# -----------------------------------------------------------------------------
# Wait for database to be ready
# -----------------------------------------------------------------------------
echo "Waiting for PostgreSQL database..."

while ! python -c "
import socket
import os
host = os.environ.get('DB_HOST', 'db')
port = int(os.environ.get('DB_PORT', 5432))
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex((host, port))
sock.close()
exit(0 if result == 0 else 1)
" 2>/dev/null; do
    echo "Database not ready, waiting..."
    sleep 2
done

echo "Database is ready!"

# -----------------------------------------------------------------------------
# Run database migrations
# -----------------------------------------------------------------------------
echo "Running database migrations..."
python manage.py migrate --noinput

# -----------------------------------------------------------------------------
# Collect static files
# -----------------------------------------------------------------------------
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# -----------------------------------------------------------------------------
# Create superuser if credentials provided
# -----------------------------------------------------------------------------
if [ -n "$DJANGO_SUPERUSER_EMAIL" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
    echo "Creating superuser..."
    python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$DJANGO_SUPERUSER_EMAIL').exists():
    User.objects.create_superuser(
        email='$DJANGO_SUPERUSER_EMAIL',
        password='$DJANGO_SUPERUSER_PASSWORD',
        first_name='${DJANGO_SUPERUSER_FIRSTNAME:-Admin}',
        last_name='${DJANGO_SUPERUSER_LASTNAME:-User}'
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
EOF
fi

# -----------------------------------------------------------------------------
# Start the application
# -----------------------------------------------------------------------------
echo "=========================================="
echo "Starting application server..."
echo "=========================================="

exec "$@"
