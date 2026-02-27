# Team Responsibilities

This section is describes the key responsibilities of each member.

## Mohammad Mahdi Farhadi (99105634)

Primary responsibilities:

1. **Docker packaging and runtime orchestration**
   The initial setup for Docker and backend dependencies exists as early commits such as `889cb45` ("add docker setup and backend dependencies") and the Compose-based structure that includes PostgreSQL.
2. **Core backend scaffolding**
   Established the Django project scaffold and the initial domain split into apps (accounts/rbac/cases/evidence/board/suspects/interrogations/trials/rewards/payments/notifications/stats).
3. **README and operational documentation (initial baseline)**
   Wrote the initial run instructions and baseline repository hygiene (`fe58b00` and related changes).

Evidence in repository:
commit author "Mohammad Mahdi" appears on the early backend foundation commits (scaffold, dependencies, and feature modules), visible in `git log`.

## Kiarash Joolaei (400100949)

Primary responsibilities:

1. **Backend hardening to match requirements and to unblock frontend**
   Fixed logical and implementation issues in the backend so that frontend development could rely on correct workflow rules and access control. Examples include:
   - Making the homepage stats endpoint explicitly public (`backend/apps/stats/views.py`, commit `01ec0d2`).
   - Enforcing case-scoped ownership/assignment access checks in workflows (e.g., `backend/apps/cases/policies.py`, `backend/apps/suspects/views.py`).
2. **Swagger/OpenAPI completeness improvements**
   Implemented domain-specific request/response examples and per-endpoint descriptions across the API surface (`backend/police_portal/schema.py`) and added regression tests to keep documentation quality from drifting (`backend/apps/stats/tests/test_stats_docs.py`), mainly in commits `01ec0d2` and `3bb278c`.
3. **Frontend development and integration**
   Implemented the React UI, role-based dashboard modules, workflow pages, and frontend testing (see `frontend/src/pages/*` and commits prefixed `feat(frontend)` and `test(frontend)`).

Evidence in repository:
commit author "KiaJJ" appears on the integration and polish commits (frontend, docs, tests, and backend fixes), visible in `git log`.

## Shared Responsibilities

- Both team members followed a consistent commit-message convention and worked in a checkpoint-driven delivery model.
- Both participated in requirement interpretation and iterative correction, as allowed by the project rubric (backend modifications during the frontend checkpoint were permitted and expected when requirement analysis gaps are found).

