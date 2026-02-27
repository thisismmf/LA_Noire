# Project Management Approach

## Task Creation

We decomposed the project into tasks that directly mirror the rubric and workflow chapters from the project description:

- Authentication and registration
- RBAC (dynamic roles + assignment)
- Case formation (complaint flow + crime scene flow)
- Evidence registration (typed evidence with validations)
- Case resolution (detective reasoning and handoff)
- Suspect identification + interrogation approvals
- Trial verdict entry
- Notifications
- Rewards/tips workflow
- Optional payment workflow (bail/fine)
- Swagger completeness and tests
- Dockerization and operational runbook

This decomposition is visible in the repository through the Django app structure (`backend/apps/*`) and through commit scopes/types (examples in [Development Conventions](Development-Conventions.md)).

## Task Distribution

- Mohammad owned the initial platform work (Docker, backend scaffolding, and baseline documentation), enabling the rest of the system to be built incrementally.
- Kiarash owned the integration work: fixing backend workflow mismatches discovered during UI work, completing frontend modules, and raising documentation/testing quality to satisfy evaluation criteria.

## Iteration and Acceptance

Acceptance criteria were taken from the rubric checklists (e.g., "complete Swagger documentation", "proper access-level verification", and specific pages/modules on frontend).

We treated tests as part of the definition-of-done:

- Backend: `pytest` + API-level flow tests and schema regression tests.
- Frontend: `vitest` + Testing Library tests for key pages and utilities.

