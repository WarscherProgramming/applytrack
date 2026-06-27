# ApplyTrack — Project Status

> Handoff snapshot for continuing development (e.g. migrating the assistant from
> Claude Code to Codex). Pairs with [ARCHITECTURE.md](ARCHITECTURE.md) and
> [CONTRIBUTING.md](CONTRIBUTING.md).

_Last updated: 2026-06-27_

## 1. Purpose

ApplyTrack is a professional-grade **job-application CRM** for an individual job
seeker. It tracks companies, applications, recruiters, interviews, and
follow-ups; manages resume and cover-letter documents with versioning; imports
and matches job-related email from Gmail; and provides a suite of **AI
assistants** (resume match, cover-letter generation, interview preparation)
built on a single shared, provider-agnostic AI platform.

The product is built **incrementally, milestone by milestone**, with production
quality at each step: strict layering, tests, and migrations.

## 2. Version / milestone status

- Backend version: `0.1.0` (`backend/pyproject.toml`)
- Frontend version: `0.1.0` (`frontend/package.json`)
- Database schema: Alembic revisions `0001` → `0010`
- Backend tests: **419 passing** (last full run), no external network calls
- Latest **committed** milestone: **M21 — AI Interview Preparation** (`84819c0`)
- Current `HEAD` includes AI Interview Preparation, including migration `0010`,
  the `interview_ai` backend feature, and the frontend Interview Prep workflow.

### Milestone history (from git)

| Milestone | Scope | State |
|----------|-------|-------|
| M1–M4 | Project scaffold, backend foundation, Docker infra, infra validation | committed |
| M5 | Companies feature | committed |
| — | Applications, Recruiters, Interviews, Follow-ups features (+ tests) | committed |
| — | Frontend foundation (app shell) | committed |
| — | Dashboard, Companies, Applications (Kanban), Recruiters UIs | committed |
| M15 | Interview Calendar (month/week/agenda) | committed |
| M16 | Gmail integration + unified email timeline | committed |
| M17 | Frontend route-level code splitting | committed |
| M18 | Resume & Cover Letter Manager (document library) | committed |
| M19A | AI Platform Foundation | committed |
| M19B | AI Resume Match | committed |
| M20 | AI Cover Letter Generator | committed |
| **M21** | **AI Interview Preparation** | **committed** |

## 3. Completed features

All routers are registered in `backend/app/main.py` under the `/api/v1` prefix.

**Core CRM**
- **Companies** — CRUD, search, uniqueness on name.
- **Applications** — CRUD, Kanban board, status pipeline; optional `resume_id` /
  `cover_letter_id` links to submitted documents.
- **Recruiters** — CRUD, contact management, company association.
- **Interviews** — scheduling + calendar (month/week/agenda views).
- **Follow-ups** — reminders with overdue/today/upcoming endpoints.
- **Dashboard** — analytics overview (charts, recent activity, upcoming items).

**Documents**
- **Resume Library** and **Cover Letter Library** — upload, version history (per
  name), download, rename, delete, metadata. Backed by a pluggable file-storage
  abstraction (local disk today).

**Gmail**
- OAuth-isolated integration that imports Inbox/Sent, detects recruiting email,
  and matches messages to companies/applications/recruiters/interviews with
  confidence scoring. **Runs in simulation mode by default** (no Google
  credentials needed); a unified email timeline is exposed in Settings.

**AI (all on the shared platform, mock provider by default)**
- **Resume Match** — resume-vs-JD analysis (score, strengths, gaps, keywords,
  suggested changes, interview topics); history + reopen.
- **AI Cover Letter** — generates Markdown + plain-text letters, saves as
  versions in the Cover Letter Library, compare/usage/regenerate.
- **AI Interview Prep** (M21) — full prep package (company overview, likely
  questions, STAR coaching, study topics, questions to ask, red flags,
  checklist); auto-saved history, reopen, compare, copy/export-PDF.
- **AI usage tracking** — every AI call is recorded in `ai_usage_records`
  (provider, model, tokens, estimated cost, latency, feature).

## 4. Current roadmap

Short term (recommended order):
1. **M22 — Authentication & Multi-User Foundation** — _the biggest gap_ (see
   §5). The app is
   currently single-user with no auth; the Settings page explicitly says
   "Authentication arrives in a later milestone."
2. **Analytics AI / insights dashboard** — leverage stored data +
   `ai_usage_records` for spend and pipeline insights.

Planned/aspirational (per `PROJECT.md` and existing scaffold stubs):
- Google Calendar integration (`integrations/google_calendar` stub exists).
- Notifications, attachments, richer analytics (feature stubs exist).
- Chrome extension for one-click application capture.

## 5. Known technical debt

**Architectural gaps**
- **No authentication / authorization.** No `users` table, no login, no per-user
  scoping on any row. All data is effectively a single implicit user. This must
  be addressed before any multi-user or production deployment.
- **Real provider paths are unverified end-to-end.** `OpenAIProvider` is unit
  tested with a mocked HTTP transport but has never run against the live OpenAI
  API; the cost table in `ai/usage_tracker.py` is a static estimate. Gmail's
  real OAuth path exists but the default is simulation — real Google credentials
  are untested.
- **AI "streaming" is simulated.** Generation is a single synchronous request;
  the UI shows an animated progress indicator, not true token streaming.
- **Storage is local-disk only.** The `FileStorage` abstraction is designed for
  cloud backends (S3/Azure/Drive) but only `LocalFileStorage` is implemented.

**Cleanup**
- **Empty scaffold directories** (created during early scaffolding, never
  implemented): `backend/app/features/{analytics, attachments, auth, emails,
  follow_ups, notifications, users}`, `backend/app/integrations/{gmail,
  google_calendar}`, `backend/app/ai/{agents, prompts, tools}`. Either implement
  or remove.
- **Name collision:** `features/follow_ups` (empty stub) vs `features/followups`
  (the real feature). Delete the stub to avoid confusion.
- **`integrations/gmail` stub is unused** — the real Gmail code lives in
  `features/gmail`.
- **`.env.example` is incomplete.** It omits the AI, storage, and Gmail settings
  that `backend/app/core/config.py` reads. All have safe defaults so the app
  runs without them, but they should be documented there. The missing keys:
  `AI_PROVIDER`, `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `AI_MODEL`,
  `AI_MAX_RETRIES`, `AI_REQUEST_TIMEOUT`, `STORAGE_BACKEND`,
  `STORAGE_LOCAL_PATH`, `STORAGE_MAX_UPLOAD_BYTES`, `GOOGLE_CLIENT_ID`,
  `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`, `GMAIL_SIMULATION`. See
  [CONTRIBUTING.md](CONTRIBUTING.md#environment-variables).
- **TypeScript build info is tracked.** `frontend/tsconfig.app.tsbuildinfo` and
  `frontend/tsconfig.node.tsbuildinfo` are generated build artifacts currently
  tracked by Git; consider removing them from the repository and ignoring
  `*.tsbuildinfo`.

**Testing / tooling**
- **No frontend tests** beyond `build` / `lint` / `typecheck` (no unit or E2E).
- **No CI pipeline** configured; tests/build are run manually.
- Migrations are **applied manually** (`alembic upgrade head`); there is no
  startup auto-migrate.
- Cosmetic: a Starlette/httpx `TestClient` deprecation warning appears in test
  output.

## 6. Quality bar / invariants (do not regress)

- Backend layering: `router → service → repository → model`, never skipped.
- Repositories never call `commit()`; the request transaction is owned by
  `get_db()`.
- Services raise `AppError` subclasses; a global handler maps them to HTTP.
- AI features depend only on the `app.ai` public surface — **no provider-specific
  code or inline prompts outside the AI layer**.
- Tests make **no real external API calls** (mock AI provider, simulated Gmail).

## 7. Next recommended milestone

**M22 — Authentication & Multi-User Foundation.**

Rationale: every other feature is built and stable, but the entire data model is
unscoped to a user and the Settings UI already advertises forthcoming auth. This
is the highest-leverage next step and unblocks deployment.

Suggested shape (consistent with existing patterns):
- `users` feature (model, repository, service, router) — reuse the existing
  `app/core/security.py` password hashing already scaffolded.
- JWT (or session) auth dependency; protect routers via a shared dependency.
- Add `user_id` ownership columns + a migration; scope all queries by user.
- Frontend: login/register, auth context, token handling in `api-client.ts`,
  route guards; flesh out the Settings → Account card.

Before starting M22, consider tackling the §5 cleanup items (delete stub dirs,
complete `.env.example`, and stop tracking generated TypeScript build info).
