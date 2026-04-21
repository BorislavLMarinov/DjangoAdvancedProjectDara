# ProjectDara

ProjectDara is a Django web application for role-based trainee learning. It includes public pages, authenticated dashboards for teachers, parents, and children, challenge gameplay, an avatar/progression system, REST API endpoints, and asynchronous achievement processing with Celery.

## Tech Stack

- Python 3.10+
- Django 5.2.13
- Django REST Framework 3.17.1
- PostgreSQL
- Celery
- Redis

## Features

- Custom user model with `teacher`, `parent`, and `child` roles
- Public home, register, and login pages
- Private dashboards and profile areas by role
- Parent-managed child account creation
- Teacher-managed challenge creation and editing
- Arithmetic, counting, pattern, and maze missions
- Avatar shop, inventory, and trainee progression
- Achievement badges and quests
- REST API endpoints for missions, trainee stats, and achievements
- Custom error pages

## Project Apps

- `accounts` - authentication, profiles, role-based access
- `challenges` - mission models, forms, gameplay, teacher CRUD
- `trainees` - progression, avatars, completions, dashboard
- `achievements` - badges, quests, async achievement processing, seed command
- `api` - DRF serializers and endpoints

## Environment Variables

Copy `.env.template` to `.env` and fill in the values.

```env
SECRET_KEY=
DEBUG=False

DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=

ALLOWED_HOSTS=

MEDIA_URL=/media/
STATIC_URL=/static/
REDIS_URL=redis://localhost:6379/0
CELERY_ALWAYS_EAGER=True
```

Notes:

- `ALLOWED_HOSTS` should be a comma-separated list, for example `127.0.0.1,localhost`.
- `CELERY_ALWAYS_EAGER=True` lets the app run without a separate Celery worker for local evaluation.
- If you want real async processing locally or in production, set `CELERY_ALWAYS_EAGER=False` and provide a working Redis instance.

## Installation

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create a PostgreSQL database and user.
4. Copy the environment template:

```bash
cp .env.template .env
```

5. Fill in your database credentials and other required values in `.env`.
6. Apply migrations:

```bash
python manage.py migrate
```

7. Create a superuser if needed:

```bash
python manage.py createsuperuser
```

8. Start the server:

```bash
python manage.py runserver
```

## Seed Demo Data

This project includes a management command that seeds demo data for evaluation:

```bash
python manage.py seed_project
```

Demo login created by the seed command:

- Username: `demo_architect`
- Password: `pass1234`

## API Endpoints

- `/api/challenges/`
- `/api/stats/`
- `/api/achievements/`

These endpoints require authentication.

## Static and Media Files

- Static files are loaded from `static/`
- Media files are stored in `media/`

For production:

```bash
python manage.py collectstatic
```

## Celery

The project is configured for Celery with `django-celery-results`.

Local evaluation can use eager mode through:

```env
CELERY_ALWAYS_EAGER=True
```

If you want background workers enabled:

```bash
celery -A ProjectDara worker -l info
```

## Tests

Run tests with:

```bash
python manage.py test
```

The test suite uses PostgreSQL, so your configured database user must be able to create a test database.

## Deployment

Before deployment:

- set `DEBUG=False`
- set a valid `ALLOWED_HOSTS`
- configure PostgreSQL credentials
- configure Redis if running Celery workers
- run `collectstatic`

Deployed project URL:

- Add your deployed URL here

## Local Evaluation Checklist

```bash
pip install -r requirements.txt
cp .env.template .env
python manage.py migrate
python manage.py seed_project
python manage.py runserver
```
