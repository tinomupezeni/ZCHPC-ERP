# ZCHPC ERP - VM Deployment

## VM IP: 10.50.14.12

## Service URLs

| Service | URL |
|---------|-----|
| **Main ERP Frontend** | http://10.50.14.12:3000 |
| **Employee Portal** | http://10.50.14.12:3001 |
| **Django API** | http://10.50.14.12:8000 |

## cPanel Reverse Proxy Setup

| Domain | Proxy To |
|--------|----------|
| `zchpcerp.zchpc.ac.zw` | `http://10.50.14.12:3000` |
| `employees.zchpc.ac.zw` | `http://10.50.14.12:3001` |

## Deployment

```bash
# 1. Edit .env
nano .env

# 2. Pull and start
docker-compose pull
docker-compose up -d

# 3. Create admin user
docker-compose exec api python manage.py createsuperuser
```
