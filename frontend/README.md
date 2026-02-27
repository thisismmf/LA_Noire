# LA Noire Frontend

React + TypeScript frontend for the Police Department project.

## Stack
- React + Vite + TypeScript
- React Router
- TanStack Query (state/data management)
- Zustand (auth persistence)
- React Flow (detective board)
- Vitest + Testing Library

## Run Locally
```bash
npm install
npm run dev
```

Frontend default URL: `http://localhost:5173`

Backend API is expected at `/api/v1` (proxied to `http://localhost:8000` in Vite dev server).

## Environment
Set optional env vars in `.env`:
```bash
VITE_API_BASE_URL=/api/v1
```

## Build and Test
```bash
npm run build
npm test
```

## Docker
Frontend container is provided via:
- `frontend/Dockerfile`
- `frontend/nginx.conf`

Run full stack:
```bash
docker compose build --no-cache web
docker compose up
```

Frontend in Docker: `http://localhost:5173`

## Implemented Modules
- Home page with stats overview
- Login/registration
- Role-based modular dashboard
- Detective board (drag/drop, red links, export image)
- Most wanted page
- Case and complaint status workflows
- General reporting + trial decision
- Evidence registration/review
- Custom admin panel for role/user management
- Tips/reward workflow
- Notification center
- Payment workflow
