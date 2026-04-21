# Production Deployment Guide

This guide covers production deployment for Afyadata.

It includes:

- manual Linux server deployment
- production Docker deployment with PostgreSQL, Gunicorn, and Nginx

## Production Environment Variables

Create a `.env` file in the project root or deployment directory.

Example:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
APP_DOMAIN=surveillance.example.org
ALLOWED_HOST=surveillance.example.org,www.surveillance.example.org,server-ip

ENGINE=django.db.backends.postgresql
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
```

Important:

- `APP_DOMAIN` is used by the Nginx container as `server_name`
- `ALLOWED_HOST` is used by Django
- in Nginx, `APP_DOMAIN` is space-separated
- in Django, `ALLOWED_HOST` is comma-separated

Examples:

- Single domain:

```env
APP_DOMAIN=afyadata.example.org
ALLOWED_HOST=afyadata.example.org
```

- Domain plus `www`:

```env
APP_DOMAIN=afyadata.example.org www.afyadata.example.org
ALLOWED_HOST=afyadata.example.org,www.afyadata.example.org
```

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
- Django + Gunicorn
- Nginx

The Nginx container reads the instance domain automatically from `.env`, so the deployer does not need to edit the Nginx config by hand.

### Production container roles

- `db`
  - image: `postgres:16-alpine`
  - stores application data
- `web`
  - built from `Dockerfile`
  - runs Django through Gunicorn
- `nginx`
  - image: `nginx:1.27-alpine`
  - serves `/static/` and `/media/`
  - reverse proxies app traffic to Gunicorn

Important:

- Gunicorn does not need a separate image in this setup
- it runs inside the `web` container through [entrypoint.sh](../entrypoint.sh)

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
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
APP_DOMAIN=surveillance.example.org
ALLOWED_HOST=surveillance.example.org,www.surveillance.example.org,server-ip

ENGINE=django.db.backends.postgresql
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120

#AFYADATA HUB
AFYADATA_HUB_URL=https://hub.afyadata.sacids.org/api/v1/projects/register/
AFYADATA_HUB_API_KEY=get-key-from-hub
CURRENT_INSTANCE_EXTERNAL_URL=domain-url
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
- `afyadata-web`
- `afyadata-nginx`

### 5. Check logs

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f db
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

### 9. How automatic domain configuration works

The production Nginx container uses:

- [deploy/nginx/default.conf](../deploy/nginx/default.conf)

In `docker-compose.prod.yml`, that file is mounted as an Nginx template:

- `/etc/nginx/templates/default.conf.template`

The official Nginx image renders that template on container startup using environment variables. That means:

- set `APP_DOMAIN` in `.env`
- start the stack
- Nginx uses that value automatically as `server_name`

No manual `vim /etc/nginx/...` step is needed for the containerized production setup.

### 10. Stop the production stack

```bash
docker compose -f docker-compose.prod.yml down
```

To also remove volumes:

```bash
docker compose -f docker-compose.prod.yml down -v
```

### 11. HTTPS on a production server

This repo currently provides HTTP deployment by default.

For HTTPS, the usual next step is one of these:

- place this stack behind a host-level Nginx or Traefik with SSL
- add Certbot on the server
- terminate TLS at a load balancer

If you want a fully containerized HTTPS path next, we can add:

- `nginx` SSL config
- Certbot companion setup
- automatic certificate renewal
