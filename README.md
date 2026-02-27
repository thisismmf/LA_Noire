# LA_Noire

Police Department Web System 

## Run (Docker)
```bash
docker compose down
docker compose up -d --build
```

Notes:
- If your network blocks Debian apt mirrors, the backend image build can fail. The recommended flow above rebuilds the `web` image cleanly.
- Frontend will be served at `http://localhost:5173` and backend at `http://localhost:8000`.
- Payment gateway is configured for Zarinpal sandbox by default in `docker-compose.yml`.
- Set your sandbox merchant id via `ZARINPAL_MERCHANT_ID` before running production-like payment tests.

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

## Zarinpal Sandbox Flow
- `POST /api/v1/payments/create/` creates a payment and returns `redirect_url` to Zarinpal StartPay.
- After payment, Zarinpal redirects to `GET /api/v1/payments/return/?payment_id=...&Authority=...&Status=OK|NOK`.
- Backend verifies transaction with Zarinpal `verify` API and updates payment status.
- `POST /api/v1/payments/callback/` also supports manual server-side verification using `payment_id`, `authority`, and optional `status`.

## Tests
```bash
pytest
```
