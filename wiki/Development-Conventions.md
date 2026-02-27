# Development Conventions

## Commit Message Format

Commit messages follow a "Conventional Commits"-style pattern:

`type(scope): short description`

Examples from `git log --oneline` include:

- `feat(frontend): implement case and complaint workflow operations`
- `feat(backend): enforce workflow ownership and role access across cases`
- `test: cover queues, access enforcement, rewards, and payment validation`
- `docs(frontend): add runbook and environment examples`
- `chore(docker): add frontend container and compose integration`

Scopes are used when a change is clearly bounded (e.g., `frontend`, `backend`, `docker`); otherwise `type:` is used.

## Naming and Code Organization

Backend (Django):

- Apps are split by domain under `backend/apps/<domain>/` (e.g., `cases`, `evidence`, `suspects`).
- Python naming follows standard conventions:
  - `PascalCase` for classes (`Case`, `CrimeSceneReport`)
  - `snake_case` for functions and variables (`can_user_access_case`, `compute_most_wanted`)
- Each app keeps the typical DRF layers co-located:
  `models.py`, `serializers.py`, `views.py`, `urls.py`, and `tests/`.

Frontend (React + TypeScript):

- Pages live in `frontend/src/pages/*Page.tsx`.
- API clients are separated as `*Api.ts` next to the page modules (e.g., `casesApi.ts`, `boardApi.ts`).
- Component and type naming follows TS conventions:
  - `PascalCase` for React components
  - `camelCase` for functions
  - explicit exported types (`RoleSlug`, `DashboardModule`)

## Error Handling and API Envelope

Backend errors are normalized into a consistent response envelope via:

- `backend/police_portal/api_exceptions.py`

This keeps frontend error handling predictable across endpoints and matches the OpenAPI descriptions used throughout the API.

## Documentation Convention (Swagger / OpenAPI)

We intentionally treated Swagger as a product requirement, not an afterthought:

- Per-endpoint narrative descriptions are included via view docstrings and `@extend_schema`.
- Domain-specific request/response examples are generated/attached through `backend/police_portal/schema.py`.
- A regression test suite ensures documentation quality stays intact (`backend/apps/stats/tests/test_stats_docs.py`).

