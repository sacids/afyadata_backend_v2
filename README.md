# Welcome to your Afyadata version 2 👋

## Description




## Prerequisites
[Python3](https://www.python.org/)

[Django Framework](https://www.djangoproject.com/)

[PostgreSQL](https://www.postgresql.org/)


## Installation
Clone Repository

```bash
git clone https://github.com/sacids/afyadata_backend_v2.git
cd afyadata_v2
```

Install Virtual environment
```bash
sudo -H pip3 install --upgrade pip
sudo -H pip3 install virtualenv
```

Create a virtual environment:
```bash
python -m virtualenv env
env/bin/activate
```

Install all dependencies:
```bash
pip install -r requirements.txt
```

Create .env file and update database settings
```bash
ALLOWED_HOST=localhost,127.0.0.1
DB_NAME=database_name
DB_USER=username
DB_PASSWORD=password
DB_HOST=127.0.0.1
DB_PORT=5432
DEBUG=True
ENGINE=django.db.backends.postgresql
```

Run migrations:
```bash
python manage.py makemigrations
python manage.py migrate
```

Create super user:
```bash
python manage.py createsuperuser
```

Load assets files to static folder:
```bash
python manage.py collectstatic
```


## License
Licensed under the 
[MIT license](https://opensource.org/license/mit/).


## Contact
For any issue please contact afyadata@sacids.org
