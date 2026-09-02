---
inclusion: always
---

# Common Rules

These rules apply to every session in this workspace.

## Project Structure

- Go backend code lives in `internal/`: a `service.go` for business logic and a `handler.go` for HTTP routes per feature.
- Shared utilities belong in `internal/shared/utils/`.
- React frontend code lives in `client/src/`: pages in `pages/`, reusable components in `components/`, and all API calls go through `services/api.js`.

## Code Style

- Add Godoc comments for all exported Go types and functions.
- Add JSDoc headers to React files.
- Reuse existing shared components and hooks before creating new ones.
- No `console.log` in the frontend; only `console.error` inside catch blocks.
- No commented-out code, no unused imports, and no committed secrets.

## Workflow

- Create a feature or fix branch off `main`; never push directly to `main`.
- Run the following before opening a pull request:
  - `make test` — Go tests must pass.
  - `make lint` — Go vet and React ESLint must pass.
  - `make build` — full frontend + backend build must succeed.
- Reference the relevant issue in PR descriptions (`Fixes #123`).
