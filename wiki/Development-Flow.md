# Development Flow Summary (What Changed and Why)

This is a condensed version of the development-flow.

## Fixing a Frontend Homepage Error (Public Stats)

Problem:
the frontend homepage calls `GET /api/v1/stats/overview/` without authentication, but the backend default permission is authenticated (`IsAuthenticated`) via `backend/police_portal/settings.py`.

Root cause:
the stats endpoint did not override the default, so anonymous users correctly received `401`, and the UI showed an error banner.

Final fix:
`backend/apps/stats/views.py` sets `permission_classes = [AllowAny]` for `StatsOverviewView` and documents the endpoint as public.

Verification:
`backend/apps/stats/tests/test_stats_docs.py` asserts the route returns `200` for anonymous requests and checks that Swagger examples are real (not placeholders).

## Swagger / OpenAPI Documentation Improvements

Goal:
meet the rubric requirement for "complete and reliable Swagger documentation (including appropriate request/response examples and full explanations)".

Key changes (repository evidence):

- Corrected authentication schema outputs by introducing structured response serializers (e.g., `backend/apps/accounts/serializers.py` and `backend/apps/accounts/views.py`).
- Wrapped refresh-token docs to produce higher quality OpenAPI (see `TokenRefreshDocsView` in `backend/apps/accounts/views.py`).
- Replaced generic placeholders with domain-specific examples via `backend/police_portal/schema.py`.
- Added a regression test suite so every operation has a description and JSON examples (`backend/apps/stats/tests/test_stats_docs.py`).

## Docker and Runtime Verification

Runtime packaging:

- `docker-compose.yml` runs PostgreSQL (`db`), Django (`web`), and the frontend container (`frontend`).
- Backend image comes from `backend/Dockerfile`.
- Frontend image comes from `frontend/Dockerfile` and serves via `frontend/nginx.conf`.

## Tests and Quality Gates

Backend:
pytest-based API and schema tests live under `backend/apps/*/tests/` and are wired via `pytest.ini`.

Frontend:
Vitest + Testing Library tests exist under `frontend/src/**` and are runnable via `npm test` (see `frontend/package.json` scripts).

