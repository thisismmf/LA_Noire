# Evaluation Criteria Mapping (What Was Required vs What We Built)

This page summarizes the evaluation expectations from the project description and points to the concrete implementation in this repository.

## Global Evaluation Expectations

### 1) Meet the documented requirements

We implemented the required workflows as domain apps and corresponding UI modules:

- Backend domain apps: `backend/apps/*` (cases, evidence, board, suspects, interrogations, trials, rewards, payments, notifications, stats, rbac, accounts)
- Frontend workflow pages: `frontend/src/pages/*Page.tsx` (cases, evidence, detective board, most wanted, reporting, tips/rewards, payments, notifications, admin panel)

### 2) Clean and maintainable code (software engineering principles)

Concrete practices in this repo:

- Layered DRF structure per app (models/serializers/views/urls/tests).
- Centralized error envelope handler (`backend/police_portal/api_exceptions.py`) to keep API behavior predictable for the UI.
- Explicit workflow policies/helpers to avoid scattered role logic (`backend/apps/cases/policies.py`, `backend/apps/suspects/utils.py`).

### 3) Commit frequency requirement (minimum 15 commits per checkpoint)

As of **February 27, 2026**, the main delivery branch (`front`) contains **52 commits** (`git rev-list --count HEAD`), and contributions are split across both team members (`git shortlog -sne HEAD`).

## Checkpoint 1 (Backend-Focused) Requirements

The description emphasizes:

- Proper error handling
- Proper access-level management
- REST principles
- Complete Swagger documentation (with meaningful examples and explanations)
- Tests (at least 5 tests in two different apps)
- Dockerization
- Aggregated statistics endpoint
- Correct most-wanted ranking and reward logic

Repository evidence:

- Error envelope: `backend/police_portal/api_exceptions.py`
- Access control defaults: `backend/police_portal/settings.py` (`IsAuthenticated` by default) and per-endpoint overrides (`AllowAny` where needed)
- RBAC and role flexibility: `backend/apps/rbac/*`
- Swagger: `drf-spectacular` wiring (`backend/police_portal/urls.py`) and schema customizations (`backend/police_portal/schema.py`)
- Swagger regression tests: `backend/apps/stats/tests/test_stats_docs.py`
- Aggregated stats endpoint: `backend/apps/stats/views.py`
- Most-wanted formula: `backend/apps/suspects/utils.py`
- Docker and Compose: `backend/Dockerfile`, `docker-compose.yml`
- Backend tests: `pytest.ini` plus multiple tests under `backend/apps/*/tests/`

## Checkpoint 2 (Frontend-Focused) Requirements

The description emphasizes:

- Role-based, responsive UI
- Modular dashboard
- Detective board, most-wanted page, case/complaint status, evidence registration/review, admin panel (non-Django admin)
- Loading indicators and error display
- Proper frontend state management
- Frontend tests (at least 5)
- Full Docker Compose packaging

Repository evidence:

- Role-based dashboard modules: `frontend/src/features/dashboard/modules.ts`
- Implemented pages: `frontend/src/pages/*Page.tsx` (see `frontend/README.md` for the module list)
- Frontend tests: `frontend/src/pages/*.test.tsx` and utility tests (run via `npm test`)
- State management:
  - Server state: React Query (`@tanstack/react-query`)
  - Client auth persistence: Zustand (`zustand`)
- Dockerization:
  - Frontend container: `frontend/Dockerfile`, `frontend/nginx.conf`
  - Compose wiring: `docker-compose.yml`

