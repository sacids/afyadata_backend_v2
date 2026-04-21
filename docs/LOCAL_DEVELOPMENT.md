# Local Development Guide

This guide is for developers running Afyadata locally for day-to-day development.

## Stack

- Python 3.13
- Django 4.x
- PostgreSQL
- Docker Compose

## Project Structure

- `config/` - Django settings, URLs, WSGI
- `apps/` - application modules
- `templates/` - shared templates
- `assets/` - static source assets
- `media/` - uploaded files

## Environment Variables

Create a `.env` file in the project root.

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

#AFYADATA HUB
AFYADATA_HUB_URL=https://hub.afyadata.sacids.org/api/v1/projects/register/
AFYADATA_HUB_API_KEY=get-key-from-hub
CURRENT_INSTANCE_EXTERNAL_URL=domain-url
AFYADATA_GLOBAL_KEY=AFYADATA_GLOBAL_KEY
```

Notes:

- `ALLOWED_HOST` is comma-separated.
- For Docker, use `DB_HOST=db`.
- For local development, keep `DEBUG=True`.

## Option 1: Python Virtual Environment

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



## Option 2: Docker Compose for Local Development

This repo also includes a default Docker stack:

- `Dockerfile`
- `docker-compose.yml`
- `.env.docker.example`

### 1. Copy the Docker env file

```bash
cp .env.docker.example .env
```

### 2. Update `.env`

At minimum set:

```env
SECRET_KEY=replace-with-a-real-secret
DEBUG=True
ALLOWED_HOST=localhost,127.0.0.1
APP_DOMAIN=localhost
DB_NAME=afyadata_db
DB_USER=afyadata
DB_PASSWORD=strong-password
DB_HOST=db
DB_PORT=5432

#AFYADATA + EMA-I INTEGRATION TEST ENVIRONMENTS
FAO_BASE_URL=change-me
FAO_AUTH_URL=change-me
FAO_CLIENT_ID=change-me
FAO_CLIENT_SECRET=change-me

#AFYADATA HUB - PUBLIC PROJECTS
AFYADATA_HUB_URL=change-me
AFYADATA_HUB_API_KEY=change-me
CURRENT_INSTANCE_EXTERNAL_URL=change-me
AFYADATA_GLOBAL_KEY=AFYADATA_GLOBAL_KEY

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
