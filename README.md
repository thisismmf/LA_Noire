# LA_Noire

Police Department Web System (Checkpoint 1 backend)

## Run (Docker)
```bash
docker compose up --build
```

## Migrations
```bash
docker compose exec web python manage.py migrate
```

## Create Superuser
```bash
docker compose exec web python manage.py createsuperuser
```

## API Docs
- Swagger UI: `/api/docs/`
- OpenAPI schema: `/api/schema/`

## Tests
```bash
pytest
```

