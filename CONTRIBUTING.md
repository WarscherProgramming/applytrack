# Contributing to ApplyTrack

Working guide for developers (and AI assistants) continuing this project. Pairs
with [PROJECT_STATUS.md](PROJECT_STATUS.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

## Prerequisites

- Docker + Docker Compose (primary workflow).
- For running tools outside Docker: Python 3.12 and Node 22.

## Environment variables

Copy `.env.example` to `.env` at the repo root before first run:

```bash
cp .env.example .env
```

`.env` is gitignored — never commit it. Generate a real secret with
`openssl rand -hex 32` for `SECRET_KEY`.

The app runs with **no external credentials**: AI defaults to the mock provider,
Gmail to simulation mode, and calendar sync to deterministic simulation mode
with an ICS no-OAuth fallback. To enable real services, set the relevant keys
(these are read by `backend/app/core/config.py` and currently **not** listed in
`.env.example` — see PROJECT_STATUS §5):

| Variable | Default | Purpose |
|----------|---------|---------|
| `AI_PROVIDER` | `mock` | `mock` or `openai` |
| `OPENAI_API_KEY` | _(empty)_ | Enables the OpenAI provider when set |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI base URL |
| `AI_MODEL` | `gpt-4o-mini` | Default model |
| `AI_MAX_RETRIES` | `2` | Transient-failure retries |
| `AI_REQUEST_TIMEOUT` | `30.0` | Per-request timeout (s) |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Auth refresh-token lifetime |
| `STORAGE_BACKEND` | `local` | File storage backend |
| `STORAGE_LOCAL_PATH` | `storage` | Local storage root (relative to `/app`) |
| `STORAGE_MAX_UPLOAD_BYTES` | `10485760` | Max upload size (10 MB) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | _(empty)_ | Real Gmail OAuth; calendar OAuth foundation reuses the client id |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/api/v1/gmail/callback` | OAuth redirect |
| `GMAIL_SIMULATION` | `true` | Use the fake Gmail client |

> If you enable real AI/Gmail, please also add these keys to `.env.example` to
> close the documentation gap noted in PROJECT_STATUS.

## Local Docker workflow

The base compose file is production-oriented; the dev overlay adds hot-reload,
source mounts, and exposed ports. Always run both files together for development.

```bash
# Build + start the full dev stack (postgres, backend, frontend)
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

# Service URLs
#   Frontend (Vite dev):  http://localhost:5173
#   Backend (FastAPI):    http://localhost:8000
#   API docs (non-prod):  http://localhost:8000/docs
#   Health:               http://localhost:8000/health
#   Postgres:             localhost:5432

# Tail logs
docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f backend

# Stop
docker compose -f docker-compose.yml -f docker-compose.dev.yml down
```

In dev, `./backend` and `./frontend/src` are bind-mounted, so backend
(`uvicorn --reload`) and frontend (Vite HMR) pick up changes automatically.

### Database migrations

Migrations are **applied manually** (there is no startup auto-migrate). After
pulling new migrations or adding one, run inside the backend container:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend alembic upgrade head
```

Creating a migration:

1. Add/modify the model and **register it in `backend/app/database/base.py`**.
2. Write a hand-authored migration in `backend/migrations/versions/` named
   `NNNN_description.py`, with the next sequential revision id, the correct
   `down_revision`, and explicit `upgrade()`/`downgrade()` (including indexes and
   FK `ondelete`). Match the style of existing migrations rather than relying on
   autogenerate.
3. `alembic upgrade head` (and verify `downgrade` is sane).

> Uploaded files in dev land in `./backend/storage/` (gitignored). In production
> they persist in the `backend_storage` Docker volume.

## Test commands

### Backend (run inside the backend container)

```bash
# Full suite
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend python -m pytest -q

# A single file / test
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend \
  python -m pytest tests/integration/features/test_interview_ai_api.py -q
```

The suite needs the dev dependencies. If a fresh container lacks them
(`pytest` not found), install once:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend pip install -e ".[dev]"
```

Tests use a separate `<db>_test` database, roll back per test, and make **no
external network calls**. The default `client` fixture authenticates as a
generated active test user; use `anonymous_client` for unauthenticated cases.
When seeding owned records directly, set `user_id=test_user.id`, and add
cross-user 404/list-isolation coverage for new user-created resources. Keep
external IO mocked: use the `MockProvider` / injected `AIClient` for AI, the
simulated Gmail client, simulated calendar provider adapters, and deterministic
auth tokens/password hashes in auth tests.

### Frontend (run inside the frontend container or locally in `frontend/`)

```bash
npm run build       # tsc -b && vite build  (the authoritative gate)
npm run lint        # eslint
npm run typecheck   # tsc --noEmit
```

There are no frontend unit/E2E tests yet; `build` (type-checks) + `lint` are the
quality gates.

## Branch workflow

- **Default branch:** `main`.
- **One branch per milestone**, named `feature/<short-name>` (history shows
  `feature/companies`, `feature/gmail-integration`, `feature/ai-platform`,
  `feature/ai-interview-prep`, …). Use `chore/...` or `perf/...` for
  non-feature work (e.g. `chore/frontend-code-splitting`).
- Branch from `main`, do the milestone, ensure the Definition of Done, then merge
  back. If a future milestone depends on unmerged work, branch from that feature
  branch or fast-forward-merge it before continuing.
- Never commit `.env` or `node_modules`. Do not commit `backend/storage/`.

## Commit style

**Conventional Commits**, with a scope, e.g.:

```
feat(ai): implement AI-powered cover letter generation
feat(gmail): integrate Gmail synchronization and unified email timeline
perf(frontend): add route-level code splitting
feat(documents): implement resume and cover letter management
```

- Type: `feat` / `fix` / `perf` / `chore` / `refactor` / `docs` / `test`.
- Scope: the feature or area (`ai`, `gmail`, `applications`, `frontend`,
  `documents`, …).
- Prefer one cohesive commit per milestone (the existing history is one commit
  per milestone). Keep messages imperative and descriptive.

## Milestone Definition of Done

A milestone is complete only when **all** of the following hold:

1. **Layering respected** — `router → service → repository → model`; repositories
   never `commit()`; services raise `AppError` subclasses.
2. **Ownership respected** — user-created records carry `user_id`, routers use
   `CurrentUser`, create paths stamp `current_user.id`, and list/get/update/delete
   paths are scoped so cross-user access returns 404.
3. **AI boundary respected** — features use only the `app.ai` public surface; no
   provider-specific code or inline prompts outside `app/ai/`; prompts added to
   the central registry.
4. **Migrations** — any schema change has a hand-written, reversible Alembic
   migration; the new model is registered in `database/base.py`;
   `alembic upgrade head` applies cleanly.
5. **Backend tests pass** — `pytest` green, including new unit + integration
   tests for the milestone. **No real external API calls** in tests.
6. **Frontend builds** — `npm run build` passes (so does `lint`/`typecheck`);
   new routes are lazy-loaded in `routes/index.tsx` and added to
   `app/navigation.ts`.
7. **Docker works** — the dev stack builds and runs; a manual end-to-end check of
   the new flow succeeds (the app must work fully offline via mock AI,
   simulated Gmail, and simulated calendar sync where applicable).
8. **No regressions** — existing tests still pass; existing features unaffected
   (notably: do not modify Gmail behaviour or revert the Vite `manualChunks`
   config).
9. **Docs** — update [PROJECT_STATUS.md](PROJECT_STATUS.md) (milestone status,
   roadmap, debt) when scope or state changes.

## Conventions cheat-sheet

- **Backend:** UUID PKs + tz-aware timestamps; enums stored as strings,
  validated in Pydantic; PATCH uses `model_dump(exclude_unset=True)`, POST uses
  `model_dump()`; ruff for lint/format (line length 100), mypy strict.
- **Frontend:** feature-sliced (`types`/`api`/`hooks`/`components`); endpoint
  URLs only in `api/`; TanStack Query with per-feature key factories; forms via
  React Hook Form + Zod; UI via shadcn/ui primitives in `components/ui/`.
- **Code references in docs/PRs:** link files as `path:line` for clickability.
