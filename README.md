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
