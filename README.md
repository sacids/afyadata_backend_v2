# Afyadata

Afyadata is a Django-based community surveillance platform for managing projects, forms, submissions, OHKR reference data, and API/mobile workflows.

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
- `docs/` - setup and deployment guides

## Documentation

Use the guide that matches your goal:

- Local development:
  - [docs/LOCAL_DEVELOPMENT.md](/docs/LOCAL_DEVELOPMENT.md)
- Production deployment:
  - [docs/PRODUCTION_DEPLOYMENT.md](/docs/PRODUCTION_DEPLOYMENT.md)

## Quick Start

### Local development

```bash
git clone https://github.com/sacids/afyadata_backend_v2.git
cd afyadata_backend_v2
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
cp .env.docker.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Production Docker

```bash
cp .env.docker.example .env
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

## Included Deployment Files

- `Dockerfile`
- `docker-compose.yml`
- `docker-compose.prod.yml`
- `.env.docker.example`
- `deploy/nginx/default.conf`

## License

Licensed under the [MIT license](https://opensource.org/license/mit/).

## Contact

For support or deployment issues, contact `afyadata@sacids.org`.
