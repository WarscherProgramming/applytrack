# ApplyTrack - Project Status

> Handoff snapshot for continuing development. Pairs with
> [ARCHITECTURE.md](ARCHITECTURE.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

_Last updated: 2026-06-27_

## 1. Purpose

ApplyTrack is a professional-grade **job-application CRM** for an individual job
seeker. It tracks companies, applications, recruiters, interviews, follow-ups,
tasks, external calendar sync, Gmail activity, resume and cover-letter versions,
and AI-assisted job-search workflows.

The product has grown into an AI-powered career platform. Resume Match, Cover
Letter AI, Interview Prep, Career Intelligence, Career Copilot, Job
Intelligence, Opportunity Discovery, Daily Briefing, and generated Tasks all
reuse the shared provider-agnostic AI platform and deterministic analytics.

The product is built incrementally, milestone by milestone, with production
quality at each step: strict layering, tests, migrations, and Docker-first
verification.

## 2. Version / Milestone Status

- Backend version: `0.1.0` (`backend/pyproject.toml`)
- Frontend version: `0.1.0` (`frontend/package.json`)
- Database schema: Alembic revisions `0001` -> `0014`
- Backend tests: **447 passing** (Docker-backed full suite), no external network
  calls.
- Latest **committed** milestone: **M28 - Task System** (`5568a9c`)
- Current `HEAD` includes Task System: manual and generated tasks, the `tasks`
  table/migration, generation from Daily Briefing/follow-ups/interviews/Gmail,
  and a Tasks frontend page.
- **M29 - Authentication is implemented in the working tree but not yet
  committed.** It adds `auth` and `users` features, `users` and
  `auth_refresh_tokens` tables, registration/login/refresh/logout/current-user
  endpoints, a protected-user dependency, login/register pages, frontend token
  handling, route guards, and account settings.

### Milestone History

| Milestone | Scope | State |
|----------|-------|-------|
| M1-M4 | Project scaffold, backend foundation, Docker infra, infra validation | committed |
| M5 | Companies feature | committed |
| - | Applications, Recruiters, Interviews, Follow-ups features (+ tests) | committed |
| - | Frontend foundation (app shell) | committed |
| - | Dashboard, Companies, Applications (Kanban), Recruiters UIs | committed |
| M15 | Interview Calendar (month/week/agenda) | committed |
| M16 | Gmail integration + unified email timeline | committed |
| M17 | Frontend route-level code splitting | committed |
| M18 | Resume & Cover Letter Manager (document library) | committed |
| M19A | AI Platform Foundation | committed |
| M19B | AI Resume Match | committed |
| M20 | AI Cover Letter Generator | committed |
| **M21** | **AI Interview Preparation** | **committed** |
| **M22** | **Career Intelligence Dashboard** | **committed** |
| **M23** | **AI Career Copilot** | **committed** |
| **M24** | **AI Job Intelligence Engine** | **committed** |
| **M25** | **Opportunity Discovery Engine** | **committed** |
| **M26** | **Daily Briefing & Notifications** | **committed** |
| **M27** | **Calendar Integration** | **committed** |
| **M28** | **Task System** | **committed** |
| **M29** | **Authentication** | **in working tree (uncommitted)** |

## 3. Completed Features

All routers are registered in `backend/app/main.py` under the `/api/v1` prefix.

**Core CRM**
- **Companies** - CRUD, search, uniqueness on name.
- **Applications** - CRUD, Kanban board, status pipeline; optional `resume_id` /
  `cover_letter_id` links to submitted documents.
- **Recruiters** - CRUD, contact management, company association.
- **Interviews** - scheduling + calendar (month/week/agenda views).
- **Follow-ups** - reminders with overdue/today/upcoming endpoints.
- **Dashboard** - analytics overview (charts, recent activity, upcoming items).

**Documents**
- **Resume Library** and **Cover Letter Library** - upload, version history,
  download, rename, delete, and metadata. Backed by a pluggable file-storage
  abstraction (local disk today).

**Gmail**
- OAuth-isolated integration that imports Inbox/Sent, detects recruiting email,
  and matches messages to companies/applications/recruiters/interviews with
  confidence scoring. It runs in simulation mode by default.

**AI and Intelligence**
- **Resume Match** - resume-vs-job-description analysis, history, and reopen.
- **AI Cover Letter** - Markdown/plain-text generation saved into the Cover
  Letter Library.
- **AI Interview Prep** (M21) - full prep packages, history, compare, copy, and
  export.
- **Career Intelligence** (M22) - deterministic job-search analytics plus AI
  recommendations over computed facts only.
- **AI Career Copilot** (M23) - proactive daily briefing and ranked priorities.
- **AI Job Intelligence Engine** (M24) - structured skill extraction,
  normalization, trends, resume gaps, and AI interpretation.
- **Opportunity Discovery Engine** (M25) - Greenhouse/Lever/Ashby/RSS provider
  adapters, normalized postings, deterministic scoring, and one-click save.
- **Daily Briefing & Notifications** (M26) - briefing, prioritized actions, and
  notification state.
- **Calendar Integration** (M27) - Google/Outlook provider foundations,
  idempotent simulation sync, and ICS export.
- **Task System** (M28) - actionable work queue with manual tasks and generated
  tasks from existing ApplyTrack signals.
- **AI usage tracking** - every AI call is recorded in `ai_usage_records`.

**Authentication**
- **Authentication** (M29) - user registration, login, JWT access tokens, hashed
  refresh-token rotation, logout revocation, current-user lookup, protected
  route dependency, frontend auth provider, token refresh handling, protected
  app shell, and account settings.

## 4. Current Roadmap

Short term (recommended order):
1. **Review and commit M29** (Authentication).
2. **User data scoping for existing records** - add user ownership columns and
   query scoping to CRM/domain tables before real multi-user deployment. This is
   intentionally separate from organizations, teams, and cloud sync.
3. **Copilot persistence** - persist pinned/completed recommendations and daily
   briefing history once authentication and user scoping exist.

Planned/aspirational:
- Real calendar OAuth token exchange and external provider writes beyond the
  M27 simulation-mode foundations.
- Attachments and richer analytics (feature stubs exist).
- Chrome extension for one-click application capture.

## 5. Known Technical Debt

**Architectural gaps**
- **No per-user ownership scoping on existing domain rows.** Authentication now
  exists, but companies, applications, recruiters, interviews, follow-ups,
  documents, Gmail records, notifications, calendar sync records, and tasks are
  still effectively single-user data until user ownership columns and scoped
  repositories are added.
- **Existing feature routers are not globally protected yet.** The frontend app
  shell is protected and new account endpoints require a current user, but the
  existing CRM/API routers still need route-level protection as part of the
  ownership-scoping pass.
- **Real provider paths are unverified end-to-end.** OpenAI, Gmail,
  Opportunity Discovery providers, and Google/Outlook calendar writes are
  covered with mocks/simulation but not live-provider validation.
- **AI streaming is simulated.** Generation is a single synchronous request; the
  UI shows progress, not true token streaming.
- **Storage is local-disk only.** The `FileStorage` abstraction is ready for
  cloud backends, but only `LocalFileStorage` is implemented.

**Cleanup**
- **Stale scaffold directories** remain from early scaffolding:
  `backend/app/features/{analytics, attachments, emails, follow_ups,
  notifications}`, `backend/app/integrations/{gmail, google_calendar}`, and
  `backend/app/ai/{agents, prompts, tools}`. The real auth/users features now
  exist; the old auth/users scaffold debt is closed.
- **Name collision:** `features/follow_ups` (empty stub) vs `features/followups`
  (the real feature).
- **`integrations/gmail` stub is unused** - the real Gmail code lives in
  `features/gmail`.
- **`.env.example` is incomplete.** It omits AI, storage, Gmail, and auth-related
  settings read by `backend/app/core/config.py`, including
  `REFRESH_TOKEN_EXPIRE_DAYS`.
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

## 6. Quality Bar / Invariants

- Backend layering: `router -> service -> repository -> model`, never skipped.
- Repositories never call `commit()`; the request transaction is owned by
  `get_db()`.
- Services raise `AppError` subclasses; a global handler maps them to HTTP.
- AI features depend only on the `app.ai` public surface.
- Auth code depends on `core/security.py`; passwords are never stored in plain
  text and refresh tokens are stored only as hashes.
- Tests make **no real external API calls** (mock AI provider, simulated Gmail,
  simulated calendar providers).

## 7. Next Recommended Milestone

**User data scoping for existing records.**

Rationale: M29 establishes identity, password hashing, token issuance, frontend
route protection, and account settings. The next production-readiness step is
to make existing domain data user-owned and to protect existing feature routers
with the shared current-user dependency.

Suggested shape:
- Add `user_id` ownership columns and indexes to existing domain tables.
- Scope repositories and services by the authenticated user.
- Protect existing feature routers with the auth dependency.
- Backfill or deterministic-seed ownership for local/dev data.
- Keep organizations, teams, and cloud sync out of scope until after single-user
  ownership is complete.
