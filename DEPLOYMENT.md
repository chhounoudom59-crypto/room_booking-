# Deployment Guide

This project can be deployed with Docker, or directly on a Linux host with Python.

## Recommended Setup

The most reliable path is Docker because the project depends on:

- Django 4.2
- MySQL
- WhiteNoise for static files
- Runtime environment variables for secrets and database settings

## Required Environment Variables

Set these before starting the app in any hosting environment:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS`
- `USE_SQLITE=False` for MySQL-based hosting
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `DJANGO_SUPERUSER_EMAIL` and `DJANGO_SUPERUSER_PASSWORD` if you want auto-created admin access

If you use the Render-specific settings, also provide:

- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

## Docker Deployment

1. Create a `.env.docker` file from the tracked template:

```bash
cp .env.docker.example .env.docker
```

On Windows PowerShell:

```powershell
Copy-Item .env.docker.example .env.docker
```

2. Review `.env.docker` values (`SECRET_KEY`, `ALLOWED_HOSTS`, database settings).
3. Start the stack:

```bash
docker-compose up --build
```

4. Open the app at `http://localhost:8000`.

The container entrypoint will:

- wait for MySQL
- run migrations
- collect static files
- create a superuser when credentials are provided
- start Gunicorn

## Linux / VPS Deployment

1. Install Python 3.11+, MySQL client libraries, and `pip`.
2. Clone the repository and create a virtual environment.
3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Export environment variables.
5. Run migrations and collect static files:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

6. Run Gunicorn:

```bash
gunicorn room_booking_system.wsgi:application --bind 0.0.0.0:8000
```

## GitHub Actions CD

The repository includes a tag-driven Docker release workflow at [`.github/workflows/cd.yml`](.github/workflows/cd.yml).

It runs when you push a release tag:

- `dev-v*` -> development image tags
- `stg-v*` -> staging image tags
- `prod-v*` -> production image tags

The workflow expects these GitHub secrets:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

It builds the image, pushes the environment-specific version tag, and also pushes the matching alias tag for that stream:

- `master` for dev
- `testing` for staging
- `production` for prod

## Render Notes

`room_booking_system/settings_render.py` is configured for MySQL. If you deploy to Render, connect it to an external MySQL service or adjust the database settings to match your host.

If you want a simpler Render deployment, switch the app to SQLite for the web service only, but keep in mind that SQLite is not ideal for production traffic.

## Validation Checklist

- `pytest`
- `python manage.py check`
- `ruff check .`
- `docker-compose up --build`
- GitHub Actions Docker Hub secrets configured for the release pipeline

## Workflow Inventory (Current)

Current workflow files in this repository:

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`

If you plan to split quality/security checks into a dedicated workflow, add a new `quality.yml` file and keep this list updated.

## Common Failures

- Missing `SECRET_KEY` will stop Django from starting.
- Missing database environment variables will prevent migrations.
- A host without MySQL support will not work with the current production settings unless you change the database backend.