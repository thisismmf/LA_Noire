# LA_Noire

Police Department Web System (Checkpoint 1 backend)

## Run (Docker)
```bash
docker compose build --no-cache web
docker compose up
```

Notes:
- If your network blocks Debian apt mirrors, the backend image build can fail. The recommended flow above rebuilds the `web` image cleanly.
- Frontend will be served at `http://localhost:5173` and backend at `http://localhost:8000`.

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

