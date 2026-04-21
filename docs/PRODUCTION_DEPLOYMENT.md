# Production Deployment Guide

This guide covers production deployment for Afyadata.

It includes:

- manual Linux server deployment
- production Docker deployment with PostgreSQL, Redis, Celery worker, Gunicorn, and Nginx


## Option 1: Manual Linux Server Deployment

This is the simplest non-Docker production path for a Linux server.

### Prerequisites

Install:

- Python 3.13
- PostgreSQL
- Nginx
- `venv`

Ubuntu example:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip postgresql postgresql-contrib nginx
```

### 1. Clone the project on the server

```bash
git clone https://github.com/sacids/afyadata_backend_v2.git /srv/afyadata
cd /srv/afyadata
```

### 2. Create virtual environment and install packages

```bash
python3 -m venv env
source env/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Create `.env`

```bash
cp .env.docker.example .env
```

Update:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOST`
- database credentials

For public projects update and verify environment variables

- `AFYADATA_HUB_URL=https://hub.afyadata.sacids.org/api/v1/projects/register/`
- `AFYADATA_HUB_API_KEY=hub-key`
- `CURRENT_INSTANCE_EXTERNAL_URL=project-domain-name`
- `AFYADATA_GLOBAL_KEY=AFYADATA_GLOBAL_KEY`

For FAO Integration update and verify test environment variables

- `FAO_BASE_URL=https://cbs-175434516411.europe-west1.run.app`
- `FAO_AUTH_URL=https://keycloak-175434516411.europe-west1.run.app/realms/master/protocol/openid-connect/token`
- `FAO_CLIENT_ID=change-me`
- `FAO_CLIENT_SECRET=change-me`

### 4. Run migrations and collect static

```bash
source env/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

### 5. Test Gunicorn manually

```bash
source env/bin/activate
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

If that works, stop it and create a systemd service.

### 6. Create systemd service

Create `/etc/systemd/system/afyadata.service`:

```ini
[Unit]
Description=Afyadata Gunicorn Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/srv/afyadata
EnvironmentFile=/srv/afyadata/.env
ExecStart=/srv/afyadata/env/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

Then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable afyadata
sudo systemctl start afyadata
sudo systemctl status afyadata
```

### 7. Configure Nginx

Create `/etc/nginx/sites-available/afyadata`:

```nginx
server {
    listen 80;
    server_name your-domain-or-server-ip;

    client_max_body_size 50M;

    location /static/ {
        alias /srv/afyadata/static/;
    }

    location /media/ {
        alias /srv/afyadata/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/afyadata /etc/nginx/sites-enabled/afyadata
sudo nginx -t
sudo systemctl restart nginx
```

### 8. Recommended production checks

```bash
python manage.py check
python manage.py check --deploy
```

## Option 2: Production Docker Deployment

Use the dedicated stack in `docker-compose.prod.yml`.

This stack includes:

- PostgreSQL
- Redis
- Celery worker
- Django + Gunicorn
- Nginx

The Nginx container reads the instance domain automatically from `.env`, so the deployer does not need to edit the Nginx config by hand.

### Production container roles

- `db`
  - image: `postgres:16-alpine`
  - stores application data
- `redis`
  - image: `redis:7-alpine`
  - acts as the Celery broker and result backend
- `web`
  - built from `Dockerfile`
  - runs Django through Gunicorn
- `celery_worker`
  - built from `Dockerfile`
  - runs background jobs with `celery -A config worker -l info`
- `nginx`
  - image: `nginx:1.27-alpine`
  - serves `/static/` and `/media/`
  - reverse proxies app traffic to Gunicorn

Important:

- Gunicorn does not need a separate image in this setup
- it runs inside the `web` container through [entrypoint.sh](../entrypoint.sh)
- Supervisor is not needed because each long-running process runs in its own container

That startup script already does:

```sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 1. Copy the production environment file

```bash
cp .env.docker.example .env
```

### 2. Set the instance domain and production secrets

Update `.env` with real production values.

At minimum:

```env
ALLOWED_HOST=domain-name.org,www.domain-name,server-ip
APP_DOMAIN=domain-name
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False

ENGINE=django.db.backends.postgresql
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120

#AFYADATA + EMA-I INTEGRATION
FAO_BASE_URL=https://cbs-175434516411.europe-west1.run.app
FAO_AUTH_URL=https://keycloak-175434516411.europe-west1.run.app/realms/master/protocol/openid-connect/token
FAO_CLIENT_ID=change-me
FAO_CLIENT_SECRET=change-me

#AFYADATA HUB - PUBLIC PROJECTS
AFYADATA_HUB_URL=https://hub.afyadata.sacids.org/api/v1/projects/register/
AFYADATA_HUB_API_KEY=change-me
CURRENT_INSTANCE_EXTERNAL_URL=change-me
AFYADATA_GLOBAL_KEY=AFYADATA_GLOBAL_KEY
```

### 3. Start the production stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### 4. Check running containers

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected services:

- `afyadata-db`
- `afyadata-redis`
- `afyadata-web`
- `afyadata-celery-worker`
- `afyadata-nginx`

### 5. Check logs

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f db
docker compose -f docker-compose.prod.yml logs -f celery_worker
```

### 6. Create the first admin user

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 7. Access the application

Once the stack is up:

- Django/Gunicorn is internal on `web:8000`
- Nginx is public on port `80`

Open:

```text
http://your-domain-or-server-ip
```

### 8. Create a Django superuser in Docker

Use this after the containers are up so you can log into `/admin`.

- For the default Docker stack:

```bash
docker compose exec web python manage.py createsuperuser
```

- For the production Docker stack:

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

You will be prompted for:

- username
- email address
- password

If you need to create the admin user later on an already-running server, run the same command again inside the existing `web` container.


### 9. Stop the production stack

```bash
docker compose -f docker-compose.prod.yml down
```

To also remove volumes:

```bash
docker compose -f docker-compose.prod.yml down -v
```
