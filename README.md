# sis

Cloud Campus Student Information System built with Django.

## Run locally

```powershell
python manage.py runserver 127.0.0.1:8000
```

Open http://localhost:8000/.

## Run with Docker

```powershell
docker compose up --build
```

The web application runs on port 8000 and PostgreSQL data is persisted in
the `postgres_data` Docker volume.

## Deploy to Render

Deploy this repository as a **Web Service**, not a Static Site. Render can use
the included `render.yaml` blueprint to install dependencies, collect static
files, run migrations, and start Gunicorn.

The Render service must have:

- Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
- Release command: `python manage.py migrate --noinput`
- Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 3`

If the generated Render URL is not `https://sis.onrender.com`, update
`ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in the Render environment variables
to match the actual hostname before deploying.
