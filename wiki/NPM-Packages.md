# NPM Packages Used (Up to 6)

The frontend uses multiple packages; this section highlights **six** that were intentionally chosen and are directly used in the shipped UI (`frontend/package.json`).

## 1) `react-router-dom`

Why it exists in this project:
role-based navigation and multiple workflow pages require routing with nested layouts and guarded routes.

## 2) `@tanstack/react-query`

Why it exists in this project:
workflow pages depend on server state (queues, case details, actions). React Query provides caching, request deduplication, loading/error states, and predictable mutation handling.

## 3) `axios`

Why it exists in this project:
provides a clean HTTP client with interceptors (useful for JWT headers and consistent error handling), used across `frontend/src/pages/*Api.ts`.

## 4) `zustand`

Why it exists in this project:
lightweight global state for auth/session persistence and cross-page shared state without introducing the overhead of larger state frameworks.

## 5) `react-hook-form` (plus `@hookform/resolvers` + `zod`)

Why it exists in this project:
complex forms (complaint submission, evidence creation, admin role/user changes) benefit from performant form state handling and declarative validation. `zod` provides typed schemas and `@hookform/resolvers` integrates them.

## 6) `reactflow`

Why it exists in this project:
the detective board requires node-like UI behavior and connections. React Flow provides interaction primitives that map cleanly onto the board workflow (drag/drop positioning and linking).

Note:
additional UI and utility packages are present (e.g., `dayjs`, `clsx`, `html-to-image`, `lucide-react`), but the list above is limited to six per the report constraint.

