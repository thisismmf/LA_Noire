# Project Overview

## Goal

Build a web-based system that digitizes police department workflows inspired by *L.A. Noire*, using:

- Front-end: React (Vite) + TypeScript
- Back-end: Django REST Framework
- Database: PostgreSQL
- Full Docker Compose packaging (db + backend + frontend)

The system implements role-based workflows for case formation, evidence registration, detective reasoning (board), suspect handling, interrogations, trial verdict entry, tips/rewards, notifications, and an optional payment flow for bail/fines.

## Repository Structure (High-Level)

- `backend/`: Django project (`police_portal`) and domain apps in `backend/apps/*`
- `frontend/`: Vite React TypeScript app with pages, API clients, state management, and tests
- `docker-compose.yml`: PostgreSQL + Django + frontend containers

## Implementation Notes That Matter For Consistency Checks

- Default backend permission is authenticated (`IsAuthenticated`), with explicit `AllowAny` only where required (e.g., login and public pages). See `backend/police_portal/settings.py`.
- Error responses are normalized into an envelope: `{ "error": { "code", "message", "details" } }` via `backend/police_portal/api_exceptions.py`.
- Swagger/OpenAPI documentation is produced by `drf-spectacular` and is enforced via regression tests in `backend/apps/stats/tests/test_stats_docs.py`.

