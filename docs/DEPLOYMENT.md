# Deployment Guide

This guide covers deploying the ZCHPC ERP system to a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Requirements](#server-requirements)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Database Setup](#database-setup)
6. [Nginx Configuration](#nginx-configuration)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Environment Variables](#environment-variables)
9. [Monitoring & Logging](#monitoring--logging)
10. [Backup Strategy](#backup-strategy)

---

## Prerequisites

- Ubuntu 20.04+ or similar Linux distribution
- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Nginx
- Certbot (for SSL)
- Git
- Supervisor or systemd (for process management)

---

## Server Requirements

### Minimum Requirements

| Resource | Specification |
|----------|---------------|
| CPU | 2 cores |
| RAM | 4 GB |
| Storage | 50 GB SSD |
| Bandwidth | 100 Mbps |

### Recommended for Production

| Resource | Specification |
|----------|---------------|
| CPU | 4+ cores |
| RAM | 8+ GB |
| Storage | 100+ GB SSD |
| Bandwidth | 1 Gbps |

---

## Backend Deployment

### 1. Clone Repository

```bash
cd /var/www
sudo git clone <repository-url> zchpc-erp
sudo chown -R www-data:www-data zchpc-erp
cd zchpc-erp/erp_project
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### 3. Configure Settings

Create production settings file:

```python
# erp_root/settings_production.py

from .settings import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'erp_db'),
        'USER': os.environ.get('DB_USER', 'erp_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# Static files
STATIC_ROOT = '/var/www/zchpc-erp/static'
MEDIA_ROOT = '/var/www/zchpc-erp/media'

# CORS
CORS_ALLOWED_ORIGINS = [
    'https://your-domain.com',
    'https://portal.your-domain.com',
]

# JWT settings (shorter for production)
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=8),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': '/var/log/zchpc-erp/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'ERROR',
            'propagate': True,
        },
    },
}
```

### 4. Environment Variables

Create `/var/www/zchpc-erp/.env`:

```bash
SECRET_KEY=your-very-secure-secret-key-here
DB_NAME=erp_db
DB_USER=erp_user
DB_PASSWORD=your-secure-db-password
DB_HOST=localhost
DB_PORT=5432
DJANGO_SETTINGS_MODULE=erp_root.settings_production
```

### 5. Collect Static Files & Migrate

```bash
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=erp_root.settings_production
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

### 6. Gunicorn Configuration

Create `/etc/systemd/system/gunicorn.service`:

```ini
[Unit]
Description=Gunicorn daemon for ZCHPC ERP
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/zchpc-erp/erp_project
Environment="PATH=/var/www/zchpc-erp/erp_project/venv/bin"
EnvironmentFile=/var/www/zchpc-erp/.env
ExecStart=/var/www/zchpc-erp/erp_project/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/gunicorn.sock \
    --access-logfile /var/log/zchpc-erp/gunicorn-access.log \
    --error-logfile /var/log/zchpc-erp/gunicorn-error.log \
    erp_root.wsgi:application

[Install]
WantedBy=multi-user.target
```

### 7. Start Gunicorn

```bash
sudo mkdir -p /var/log/zchpc-erp
sudo chown www-data:www-data /var/log/zchpc-erp
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

---

## Frontend Deployment

### ERP Admin Frontend

```bash
cd /var/www/zchpc-erp/zchpc-erp-synergy-main

# Install dependencies
npm ci --production

# Create production environment file
cat > .env.production << EOF
VITE_API_URL=https://api.your-domain.com/api
EOF

# Build for production
npm run build

# Output is in dist/ directory
```

### Employee Portal Frontend

```bash
cd /var/www/zchpc-erp/employee-portal

# Install dependencies
npm ci --production

# Create production environment file
cat > .env.production << EOF
VITE_API_URL=https://api.your-domain.com/api
EOF

# Build for production
npm run build

# Output is in dist/ directory
```

---

## Database Setup

### 1. Install PostgreSQL

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

### 2. Create Database and User

```bash
sudo -u postgres psql

CREATE DATABASE erp_db;
CREATE USER erp_user WITH ENCRYPTED PASSWORD 'your-secure-password';
ALTER ROLE erp_user SET client_encoding TO 'utf8';
ALTER ROLE erp_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE erp_user SET timezone TO 'Africa/Harare';
GRANT ALL PRIVILEGES ON DATABASE erp_db TO erp_user;
\q
```

### 3. Configure PostgreSQL for Remote Connections (if needed)

Edit `/etc/postgresql/14/main/postgresql.conf`:
```
listen_addresses = '*'
```

Edit `/etc/postgresql/14/main/pg_hba.conf`:
```
host    erp_db    erp_user    your-server-ip/32    md5
```

```bash
sudo systemctl restart postgresql
```

---

## Nginx Configuration

### Main Configuration

Create `/etc/nginx/sites-available/zchpc-erp`:

```nginx
# API Server
server {
    listen 80;
    server_name api.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/api.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Static files
    location /static/ {
        alias /var/www/zchpc-erp/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/zchpc-erp/media/;
        expires 7d;
    }

    # API proxy
    location / {
        proxy_pass http://unix:/run/gunicorn.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 300s;
        proxy_read_timeout 300s;
    }
}

# ERP Admin Frontend
server {
    listen 80;
    server_name erp.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name erp.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/erp.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/erp.your-domain.com/privkey.pem;

    root /var/www/zchpc-erp/zchpc-erp-synergy-main/dist;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }
}

# Employee Portal Frontend
server {
    listen 80;
    server_name portal.your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name portal.your-domain.com;

    ssl_certificate /etc/letsencrypt/live/portal.your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/portal.your-domain.com/privkey.pem;

    root /var/www/zchpc-erp/employee-portal/dist;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript;

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/zchpc-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificates
sudo certbot --nginx -d api.your-domain.com
sudo certbot --nginx -d erp.your-domain.com
sudo certbot --nginx -d portal.your-domain.com

# Auto-renewal (cron job is set up automatically)
sudo certbot renew --dry-run
```

---

## Environment Variables

### Backend (.env)

```bash
# Django
SECRET_KEY=your-50-character-random-secret-key
DJANGO_SETTINGS_MODULE=erp_root.settings_production
DEBUG=False
ALLOWED_HOSTS=api.your-domain.com

# Database
DB_NAME=erp_db
DB_USER=erp_user
DB_PASSWORD=your-secure-db-password
DB_HOST=localhost
DB_PORT=5432

# Email (optional)
EMAIL_HOST=smtp.your-email-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@your-domain.com
EMAIL_HOST_PASSWORD=email-password
```

### Frontend (.env.production)

```bash
# ERP Admin
VITE_API_URL=https://api.your-domain.com/api

# Employee Portal
VITE_API_URL=https://api.your-domain.com/api
```

---

## Monitoring & Logging

### Log Locations

| Log | Path |
|-----|------|
| Django | `/var/log/zchpc-erp/django.log` |
| Gunicorn Access | `/var/log/zchpc-erp/gunicorn-access.log` |
| Gunicorn Error | `/var/log/zchpc-erp/gunicorn-error.log` |
| Nginx Access | `/var/log/nginx/access.log` |
| Nginx Error | `/var/log/nginx/error.log` |
| PostgreSQL | `/var/log/postgresql/postgresql-14-main.log` |

### Log Rotation

Create `/etc/logrotate.d/zchpc-erp`:

```
/var/log/zchpc-erp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    postrotate
        systemctl reload gunicorn
    endscript
}
```

### Health Check Endpoint

Add to Django views:

```python
# health_check/views.py
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        connection.ensure_connection()
        return JsonResponse({'status': 'healthy'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=500)
```

### Monitoring Tools (Recommended)

- **Uptime Monitoring:** UptimeRobot, Pingdom
- **Application Monitoring:** Sentry (Django integration)
- **Server Monitoring:** Prometheus + Grafana, Netdata

---

## Backup Strategy

### Database Backup Script

Create `/opt/scripts/backup-db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/var/backups/zchpc-erp"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_NAME="erp_db"
DB_USER="erp_user"

mkdir -p $BACKUP_DIR

# Database backup
PGPASSWORD="${DB_PASSWORD}" pg_dump -U $DB_USER -h localhost $DB_NAME | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Media files backup
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" -C /var/www/zchpc-erp media

# Delete backups older than 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

### Cron Job

```bash
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/scripts/backup-db.sh >> /var/log/zchpc-erp/backup.log 2>&1
```

### Restore Procedure

```bash
# Restore database
gunzip < /var/backups/zchpc-erp/db_YYYYMMDD_HHMMSS.sql.gz | psql -U erp_user erp_db

# Restore media files
tar -xzf /var/backups/zchpc-erp/media_YYYYMMDD_HHMMSS.tar.gz -C /var/www/zchpc-erp/
```

---

## Update Procedure

### Backend Update

```bash
cd /var/www/zchpc-erp/erp_project
source venv/bin/activate

# Pull latest code
git pull origin main

# Install new dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart Gunicorn
sudo systemctl restart gunicorn
```

### Frontend Update

```bash
# ERP Admin
cd /var/www/zchpc-erp/zchpc-erp-synergy-main
git pull origin main
npm ci --production
npm run build

# Employee Portal
cd /var/www/zchpc-erp/employee-portal
git pull origin main
npm ci --production
npm run build
```

---

## Troubleshooting

### Gunicorn Won't Start

```bash
# Check logs
sudo journalctl -u gunicorn -n 50

# Check socket
sudo ls -la /run/gunicorn.sock

# Test manually
cd /var/www/zchpc-erp/erp_project
source venv/bin/activate
gunicorn erp_root.wsgi:application --bind 0.0.0.0:8000
```

### 502 Bad Gateway

1. Check if Gunicorn is running: `sudo systemctl status gunicorn`
2. Check Nginx error log: `sudo tail -f /var/log/nginx/error.log`
3. Verify socket permissions

### Database Connection Issues

```bash
# Test connection
psql -h localhost -U erp_user -d erp_db

# Check PostgreSQL status
sudo systemctl status postgresql

# Check pg_hba.conf for authentication rules
```

### Static Files Not Loading

```bash
# Verify STATIC_ROOT
python manage.py collectstatic --noinput

# Check Nginx configuration
sudo nginx -t

# Check file permissions
ls -la /var/www/zchpc-erp/static/
```
