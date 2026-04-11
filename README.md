# Afyadata

Afyadata is a Django-based community surveillance platform for managing projects, forms, submissions, OHKR reference data, and API/mobile workflows.

This guide covers:

- local developer setup
- manual server deployment
- Docker deployment

## Stack

- Python 3.13
- Django 4.x
- PostgreSQL
- Gunicorn
- Docker Compose

## Project Structure

- `config/` - Django settings, URLs, WSGI
- `apps/` - application modules
- `templates/` - shared templates
- `assets/` - static source assets
- `media/` - uploaded files

## Environment Variables

Create a `.env` file in the project root. The application reads these values from `config/settings.py`.

Example:

```env
SECRET_KEY=change-me
DEBUG=True
ALLOWED_HOST=127.0.0.1,localhost

ENGINE=django.db.backends.postgresql
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=change-me
DB_HOST=127.0.0.1
DB_PORT=5432

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
```

Notes:

- `ALLOWED_HOST` is comma-separated.
- For Docker, use `DB_HOST=db`.
- For production, set `DEBUG=False`.

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/sacids/afyadata_backend_v2.git
cd afyadata_backend_v2
```

### 2. Create a virtual environment

```bash
python3 -m venv env
source env/bin/activate
```

### 3. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Prepare PostgreSQL

Create a PostgreSQL database and user, then update `.env`.

Example:

```sql
CREATE DATABASE afyadata_db;
CREATE USER afyadata WITH PASSWORD 'change-me';
GRANT ALL PRIVILEGES ON DATABASE afyadata_db TO afyadata;
```

### 5. Run database migrations

```bash
python manage.py migrate
```

### 6. Create an admin user

```bash
python manage.py createsuperuser
```

### 7. Collect static files

```bash
python manage.py collectstatic --noinput
```

### 8. Start the development server

```bash
python manage.py runserver
```

Open:

- App: `http://127.0.0.1:8000`
- Admin: `http://127.0.0.1:8000/admin`

## Manual Server Deployment

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

## Docker Deployment

This project already includes:

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env.docker.example`
- `deploy/nginx/default.conf`

### 1. Copy the Docker env file

```bash
cp .env.docker.example .env
```

### 2. Update `.env`

At minimum set:

```env
SECRET_KEY=replace-with-a-real-secret
DEBUG=False
ALLOWED_HOST=your-domain.com,server-ip
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432
```

### 3. Build and start the containers

```bash
docker compose up --build -d
```

### 4. Check logs

```bash
docker compose logs -f web
docker compose logs -f db
```

### 5. Create a superuser

```bash
docker compose exec web python manage.py createsuperuser
```

### 6. Stop the stack

```bash
docker compose down
```

To also remove database data:

```bash
docker compose down -v
```

## Docker Deployment Behind Nginx

For production, use the dedicated stack in `docker-compose.prod.yml`.

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

- Gunicorn does not need a separate image in this setup.
- It runs inside the `web` container through [entrypoint.sh](entrypoint.sh).

That startup script already does:

```sh
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

### 1. Prepare production environment

```bash
cp .env.docker.example .env
```

Update `.env` with real production values:

```env
SECRET_KEY=replace-with-a-long-random-secret
DEBUG=False
ALLOWED_HOST=your-domain.com,www.your-domain.com,server-ip

ENGINE=django.db.backends.postgresql
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

GUNICORN_WORKERS=3
GUNICORN_TIMEOUT=120
```

### 2. Build and start the production stack

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

### 3. Check running containers

```bash
docker compose -f docker-compose.prod.yml ps
```

Expected services:

- `afyadata-db`
- `afyadata-web`
- `afyadata-nginx`

### 4. Check logs

```bash
docker compose -f docker-compose.prod.yml logs -f web
docker compose -f docker-compose.prod.yml logs -f nginx
docker compose -f docker-compose.prod.yml logs -f db
```

### 5. Create the first admin user

```bash
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### 6. Access the application

Once the stack is up:

- Django/Gunicorn is internal on `web:8000`
- Nginx is public on port `80`

Open:

```text
http://your-server-ip
```

### 7. Stop the production stack

```bash
docker compose -f docker-compose.prod.yml down
```

To also remove volumes:

```bash
docker compose -f docker-compose.prod.yml down -v
```

### 8. Nginx configuration

The production Nginx container uses:

- [deploy/nginx/default.conf](deploy/nginx/default.conf)

It is responsible for:

- serving static files from `/app/static/`
- serving media files from `/app/media/`
- proxying all app traffic to the `web` container

### 9. HTTPS on a production server

This repo currently provides HTTP deployment by default.

For HTTPS, the usual next step is one of these:

- place this stack behind a host-level Nginx or Traefik with SSL
- add Certbot on the server
- terminate TLS at a load balancer

If you want a fully containerized HTTPS path next, we can add:

- `nginx` SSL config
- Certbot companion setup
- automatic certificate renewal

If you want public access through Nginx on the host:

- keep Django running on `127.0.0.1:8000` or map container port `8000`
- reverse proxy requests from Nginx to the Django container
- keep `ALLOWED_HOST` aligned with your domain

## Common Commands

### Run migrations

```bash
python manage.py migrate
```

### Create a superuser

```bash
python manage.py createsuperuser
```

### Collect static files

```bash
python manage.py collectstatic --noinput
```

### Run deployment checks

```bash
python manage.py check --deploy
```

## Troubleshooting

### Database connection fails

Check:

- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- PostgreSQL service/container status

### Static files are missing

Run:

```bash
python manage.py collectstatic --noinput
```

### Docker container starts but app is unavailable

Check:

```bash
docker compose logs -f web
```

The web container entrypoint already runs:

- `python manage.py migrate --noinput`
- `python manage.py collectstatic --noinput`
- `gunicorn config.wsgi:application`

### Permission or media upload issues

Make sure the process user can write to:

- `media/`
- `static/`

## License

Licensed under the [MIT license](https://opensource.org/license/mit/).

## Contact

For support or deployment issues, contact `afyadata@sacids.org`.
