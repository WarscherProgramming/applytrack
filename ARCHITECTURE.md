# ApplyTrack — Architecture

> Technical reference for the codebase. Pairs with
> [PROJECT_STATUS.md](PROJECT_STATUS.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

## Overview

A two-service application plus PostgreSQL, orchestrated by Docker Compose:

```
frontend (React/Vite)  ──HTTP /api/v1──>  backend (FastAPI)  ──>  PostgreSQL
                                                │
                                                ├─ AI platform (mock | OpenAI)
                                                ├─ File storage (local disk)
                                                └─ Gmail (simulation | Google)
```

- **Backend:** Python 3.12, FastAPI, SQLAlchemy 2.0 (sync), Alembic, Pydantic v2.
- **Frontend:** React 19, TypeScript, Vite 6, TanStack Query v5, React Router v6,
  React Hook Form + Zod, Tailwind + shadcn/ui (Radix), Recharts, date-fns.
- **DB:** PostgreSQL 16.

---

## Backend architecture

### Feature-sliced layering

Each feature lives in `backend/app/features/<name>/` and follows strict layering.
A request flows **router → service → repository → model**, and the layers never
skip:

- **`router.py`** — FastAPI routes, request/response schemas, dependency wiring.
  Thin; delegates to a service. Builds the service via a `Depends(get_db)`-based
  factory.
- **`service.py`** — business logic. Validates cross-entity rules, orchestrates
  repositories, raises `AppError` subclasses. Never touches HTTP.
- **`repository.py`** — data access. Subclasses `app/shared/base_repository.py`
  (`BaseRepository[Model]` with `get/get_or_raise/get_all/create/update/delete`)
  and adds query methods (e.g. `list_paginated`). **Never calls `commit()`** —
  only `flush()`.
- **`model.py`** — SQLAlchemy models, subclassing `app/shared/base_model.py`
  (`BaseModel`: UUID PK + timezone-aware `created_at`/`updated_at`).
- **`schema.py` / `schemas.py`** — Pydantic models, subclassing
  `app/shared/base_schema.py` (`AppBaseModel` with `from_attributes`).

### Cross-cutting infrastructure (`backend/app/`)

- **`main.py`** — app factory; registers every router under `settings.API_V1_PREFIX`
  (`/api/v1`); registers exception handlers; CORS; a `/health` endpoint.
- **`core/config.py`** — `pydantic-settings` `Settings` loaded from `.env`
  (DB, security, CORS, AI, storage, Gmail). Exposes derived properties such as
  `ai_active_provider`, `ai_configured`, `gmail_simulation`, `is_production`.
- **`core/logging.py`, `core/security.py`** — logging config; password hashing.
- **`database/session.py`** — engine + `SessionLocal`; **`get_db()` owns the
  transaction**: it `commit()`s on success and `rollback()`s on any exception.
  This is why repositories only `flush()`.
- **`database/base.py`** — imports every model so Alembic autogenerate and the
  test harness see them. **Add new models here.**
- **`exceptions/http.py`** — `AppError` base + `NotFoundError` (404),
  `ConflictError` (409), `ValidationError` (422), `UnauthorizedError` (401),
  `ForbiddenError` (403). Each carries a `status_code`.
- **`exceptions/handlers.py`** — global handlers mapping `AppError` (and pydantic
  errors) to JSON responses. Business code raises typed errors and stays
  HTTP-agnostic.
- **`shared/`** — reusable bases: `base_model`, `base_repository`, `base_schema`,
  plus the `documents/` and `storage/` subsystems (below).

### Registered features

`companies`, `applications`, `recruiters`, `interviews`, `followups`, `gmail`,
`resumes`, `cover_letters`, `resume_match`, `cover_letter_ai`, `interview_ai`.

> **Scaffold stubs (not implemented):** `features/{analytics, attachments, auth,
> emails, follow_ups, notifications, users}`, `integrations/{gmail,
> google_calendar}`, `ai/{agents, prompts, tools}`. See PROJECT_STATUS §5. Note
> `follow_ups` (stub) is distinct from `followups` (real).

---

## Frontend architecture

### Feature-sliced structure (`frontend/src/`)

Mirrors the backend. Each feature in `features/<name>/` typically has:

- **`types/` (or `types.ts`)** — TS interfaces mirroring backend schemas.
- **`api/` (or `api.ts`)** — typed wrappers over the shared Axios client. The
  **only** place endpoint URLs live; components/hooks never call Axios directly.
- **`hooks/` (or `hooks.ts`)** — TanStack Query hooks with a **query-key
  factory** per feature and precise invalidation. `keepPreviousData` for lists.
- **`components/`** — feature UI.

Shared layers:
- **`services/api-client.ts`** — central Axios instance. Base URL is
  `VITE_API_URL` + `/api/v1` in dev, or relative `/api/v1` in prod (nginx
  proxies). Normalises error `status`.
- **`components/ui/`** — shadcn/ui primitives (Radix + Tailwind + CVA).
- **`components/common/`, `components/layout/`** — shared composite components
  and the app shell (sidebar, topbar).
- **`pages/`** — one component per route.
- **`routes/index.tsx`** — `createBrowserRouter`; **every page is `React.lazy`**
  for code splitting, with a single `<Suspense>` boundary around `<Outlet />` in
  the layout. **Add new routes here.**
- **`app/navigation.ts`** — sidebar nav items. **Add new nav entries here.**
- **`app/providers.tsx`** — QueryClient, theme, tooltip, toast providers.

### State & data fetching

- **Server state:** TanStack Query (caching, invalidation, optimistic UX).
- **Form state:** React Hook Form + Zod resolver; schemas mirror backend
  constraints for instant validation.
- **No global client-state library** — local component state + query cache.

### Build / bundling

`vite.config.ts` defines `build.rollupOptions.output.manualChunks` to split
heavy vendors (`react`, `charts`/recharts, `query`). Combined with per-route
`React.lazy`, the initial bundle stays small. **Do not revert the manualChunks
config.**

---

## Database & migration approach

- **PostgreSQL 16**, accessed via SQLAlchemy 2.0 (sync, typed `Mapped[...]`).
- **UUID primary keys** and **timezone-aware timestamps** on every model
  (`BaseModel`).
- **Enums are stored as plain strings** (`String(50)`) with the constraint
  enforced in Pydantic, not the DB — so adding enum values never requires
  `ALTER TYPE` on a production table.
- **Alembic** migrations live in `backend/migrations/versions/`, numbered
  `0001`…`0010`, each with explicit `upgrade()`/`downgrade()` and a linear
  `down_revision` chain. Migrations are **hand-written** (not blindly
  autogenerated) for control over FK `ondelete` behaviour and indexes.
- **FK delete policy** is deliberate per relationship: `CASCADE` for owned
  children (e.g. interviews → application), `RESTRICT` to protect referenced rows
  (applications → company), `SET NULL` to preserve history (AI history/email/
  document links). New models register in `database/base.py`.
- Migrations are applied manually: `alembic upgrade head` inside the backend
  container (see CONTRIBUTING). The test harness builds the schema from models
  via `Base.metadata.create_all` against a separate `*_test` database.

Current tables: `companies`, `job_applications`, `recruiters`, `interviews`,
`followups`, `gmail_accounts`, `email_messages`, `resumes`, `cover_letters`,
`ai_usage_records`, `resume_match_analyses`, `interview_prep_packages`.

---

## AI platform architecture (`backend/app/ai/`)

A small, **provider-agnostic** layer that all AI features consume. Feature code
depends only on the public surface re-exported from `app/ai/__init__.py` — never
on a concrete provider, the retry policy, or the usage table.

| Module | Role |
|--------|------|
| `provider.py` | `AIProvider` ABC — the single seam. `generate(GenerationRequest) -> ProviderResponse`. |
| `mock_provider.py` | `MockProvider` — deterministic, offline; supports canned responses, a handler, and simulated transient failures. **Default provider.** |
| `openai_provider.py` | `OpenAIProvider` — httpx-based adapter, lazily imported, only used when an API key is configured. |
| `schemas.py` | `GenerationRequest`, `ProviderResponse`, `TokenUsage`, `AIResult`, `StructuredResult`. |
| `prompt_templates.py` | Central named-prompt registry (`render_template`, `register_template`). Prompts use `{{ var }}` delimiters so literal `{}`/JSON in prompts survive. **All prompts live here.** |
| `prompt_renderer.py` | `{{ var }}` interpolation with required-variable validation. |
| `response_parser.py` | `parse_json` / `parse_model` — strips code fences, validates against a Pydantic schema, raises `AIResponseError` on bad output. |
| `retry.py` | `retry_call` — exponential backoff, retries **only** `AITransientError`. |
| `usage_tracker.py` | `AIUsageRecord` model + `estimate_cost` + `UsageTracker.record` (flush-only persistence). |
| `client.py` | `AIClient` — orchestrates model defaulting → retry → latency timing → cost estimate → usage persistence. `generate()` and `generate_structured(schema)`. |
| `errors.py` | `AIError` (subclasses `AppError`) → `AIConfigurationError`, `AIProviderError`, `AITransientError` (retryable), `AIResponseError`, `PromptRenderError`. |
| `__init__.py` | `get_ai_provider()` / `get_ai_client()` factories that read config. |

### Provider selection

`settings.ai_active_provider` returns `"openai"` **only** when
`AI_PROVIDER=openai` **and** `OPENAI_API_KEY` is set; otherwise `"mock"`. The app
therefore always runs with no credentials and never makes an accidental external
call.

### Per-feature "simulation" pattern

Each AI feature ships a `simulation.py` producing realistic, feature-shaped
output. In mock mode the feature service seeds a `MockProvider` with a handler
returning that simulated JSON — but the request **still flows through
`generate_structured`** (parsing + usage tracking). Nothing bypasses the
abstraction, and the UI works fully offline.

### Feature integration shape (resume_match, cover_letter_ai, interview_ai)

```
service: gather inputs (resume text, application/company context, …)
   → render_template("<feature>.v1", vars)
   → AIClient.generate_structured(GenerationRequest, <ResultSchema>, db, feature="<name>")
   → persist (own history table, or the Cover Letter Library for cover_letter_ai)
```

- **resume_match** and **interview_ai** persist to their own history tables
  (`resume_match_analyses`, `interview_prep_packages`).
- **cover_letter_ai** has **no table** — generated letters are saved as versions
  in the existing Cover Letter Library (the document system provides versioning).
- AI clients are **injectable** (`ai_client=...`) so tests pass a deterministic
  mock; the API path is exercised by overriding the router's `_get_service`
  dependency.

---

## Gmail integration architecture (`backend/app/features/gmail/`)

Built to keep provider specifics isolated and to run without real credentials.

| Module | Role |
|--------|------|
| `oauth.py` | OAuth 2.0 via httpx (authorization URL, code exchange, refresh). Isolated; raises `OAuthNotConfiguredError`. |
| `gmail_client.py` | `GmailClient` ABC + `FakeGmailClient` (seeds realistic job emails) + `GoogleGmailClient` (Gmail REST via httpx). `get_gmail_client()` factory. |
| `email_matcher.py` | **Pure, testable** matching: domain/known-company detection, recruiting-email heuristics, confidence scoring, thread inheritance. No DB/IO. |
| `token_crypto.py` | Fernet encryption of stored tokens (key derived from `SECRET_KEY`). Refresh/access tokens stored encrypted; **passwords never stored.** |
| `models.py` | `GmailAccount`, `EmailMessage` (JSONB recipients/labels/attachments; match FKs `SET NULL`; `account_id` `CASCADE`). |
| `repository.py`, `schemas.py`, `service.py`, `router.py` | Standard feature layers; sync/status/connect/callback/disconnect/list/timeline. |

**Simulation mode** (`GMAIL_SIMULATION=true`, the default, or whenever Google
creds are absent) uses `FakeGmailClient` so the whole connect → sync → match →
timeline pipeline works locally. The matcher is independently unit-tested. The
AI Interview Prep feature reuses `EmailMessageRepository.list_filtered(application_id=…)`
to pull recent related emails as grounding context.

---

## Document / resume system architecture

A generic, versioned document subsystem powers both the Resume and Cover Letter
libraries, plus a storage abstraction designed for future cloud backends.

### Storage abstraction (`backend/app/shared/storage/`)

- `base.py` — `FileStorage` ABC (`save/load/delete/exists`) keyed by an opaque,
  backend-relative **key** (e.g. `resumes/<uuid>.pdf`), never a host path. Plus
  `StorageError` / `FileNotFoundInStorageError`.
- `local.py` — `LocalFileStorage` writing under `STORAGE_LOCAL_PATH`, with
  path-traversal confinement.
- `__init__.py` — `get_storage()` factory (the single seam). Adding S3/Azure/
  Drive = a new class + one branch here; **no service/router/model changes.**

### Shared document base (`backend/app/shared/documents/`)

- `model.py` — `DocumentBase` (abstract): `name`, `file_name`, `storage_path`,
  `version`, `notes` (+ `BaseModel` id/timestamps).
- `repository.py` — `DocumentRepository`: `next_version(name)` (per-name
  auto-increment) + name/query-filtered listing.
- `service.py` — `DocumentService`: validates upload (extension allowlist incl.
  `.pdf/.docx/.txt/.md/...`, size cap), generates the storage key, writes the
  row then the blob (so a failed write rolls back the row), and exposes
  `upload/get/list/download/update/delete`. `download()` returns
  `DownloadedDocument(record, content)`.
- `router.py` — `build_document_router(...)` factory: multipart upload + streamed
  download + CRUD, reused by both libraries.

### Feature wrappers

`features/resumes/` and `features/cover_letters/` are thin: a concrete model
(`Resume` / `CoverLetter`) on `DocumentBase`, a repository, a `DocumentService`
subclass (with `storage_prefix`), shared schemas, and a router from the factory.
Versions are grouped by `name`; uploading the same name creates the next version.

**Text extraction** for AI features lives in
`features/resume_match/text_extraction.py` (`extract_text`): PDF via `pypdf`,
DOCX/ODT via `zipfile`+XML strip, TXT/MD/RTF via decode, with a char cap; raises
`ResumeTextExtractionError` (422) for unsupported/empty input. Reused by
cover_letter_ai (templates) and interview_ai.

---

## Testing strategy

- **Framework:** `pytest` (+ `httpx` for the FastAPI `TestClient`). Config in
  `backend/pyproject.toml` (`testpaths = ["tests"]`).
- **Layout:** `tests/unit/...` (pure logic: AI platform, prompt rendering, JSON
  parsing, retry, usage, email matcher, text extraction, service logic with
  mocked repos) and `tests/integration/...` (FastAPI `TestClient` against a real
  test database).
- **Isolation:** `tests/conftest.py` creates a separate `<db>_test` database
  once per session and builds the schema from models. Each test gets a `db`
  session fixture that **rolls back** after the test, so tests never commit and
  start clean. The `client` fixture overrides `get_db` to share that session.
- **AI testing:** the `MockProvider` and injectable `AIClient` make AI
  deterministic; the API path is tested by overriding the router's
  `_get_service`. `OpenAIProvider` is tested with an `httpx.MockTransport`.
  **No test makes a real external API call** (AI or Gmail).
- **Current status:** 419 passing.
- **Frontend:** no unit/E2E tests yet; quality gates are `npm run build`
  (includes `tsc -b`), `npm run lint`, `npm run typecheck`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for exact commands.
