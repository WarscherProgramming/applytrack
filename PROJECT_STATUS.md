# ApplyTrack - Project Status

> Handoff snapshot for continuing development. Pairs with
> [ARCHITECTURE.md](ARCHITECTURE.md) and [CONTRIBUTING.md](CONTRIBUTING.md).

_Last updated: 2026-06-28_

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
- Database schema: Alembic revisions `0001` -> `0016`
- Backend tests: **455 passing** (Docker-backed full suite), no external network
  calls.
- Latest **committed** milestone: **M32 - CI/CD Pipeline** (`43688b7`)
- Current `HEAD` includes CI validation: GitHub Actions backend/frontend/Docker
  CI, dependency caching, PostgreSQL-backed migration/test execution, frontend
  lint configuration, Docker Compose validation, README status badge, and CI
  docs.
- **M33A - Deployment Preparation is implemented in the working tree but not
  yet committed.** It adds Render/Vercel deployment preparation, complete
  environment documentation, production CORS guardrails, explicit frontend API
  configuration guidance, migration guidance, and `DEPLOYMENT.md`.

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
| **M29** | **Authentication** | **committed** |
| **M30** | **User Data Ownership & Query Scoping** | **committed** |
| **M31** | **Settings & Security** | **committed** |
| **M32** | **CI/CD Pipeline** | **committed** |
| **M33A** | **Deployment Preparation** | **in working tree (uncommitted)** |

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
- **User Data Ownership** (M30) - existing user-created domain records are owned
  by `users.id`, existing feature routers require the current-user dependency,
  create paths stamp `current_user.id`, list/read/update/delete paths are scoped
  by owner, and cross-user direct access returns 404.
- **Settings & Security** (M31) - account profile settings, timezone and
  notification preferences, app preferences, strong password changes,
  refresh-token-backed session actions, scoped JSON export, and a frontend
  settings center.
- **CI/CD Pipeline** (M32) - GitHub Actions workflow for backend tests and
  migrations, frontend build/lint/typecheck, Docker image builds, and Docker
  Compose config validation.

**Deployment Preparation**
- **Deployment Preparation** (M33A) - Vercel/Render prep files, complete
  `.env.example`, production CORS guardrails, explicit OAuth redirect settings,
  migration guidance, smoke-test checklist, rollback notes, and documented local
  file-storage limitation.

## 4. Current Roadmap

Short term (recommended order):
1. **Review and commit M33A** (Deployment Preparation).
2. **Copilot persistence** - persist pinned/completed recommendations and daily
   briefing history once authentication and user scoping exist.

Planned/aspirational:
- Real calendar OAuth token exchange and external provider writes beyond the
  M27 simulation-mode foundations.
- Attachments and richer analytics (feature stubs exist).
- Chrome extension for one-click application capture.

## 5. Known Technical Debt

**Architectural gaps**
- **No organizations/teams yet.** M30 establishes single-user ownership and
  query scoping only, and M31 adds individual account settings only; shared
  workspaces, orgs, roles, billing, and cloud sync remain out of scope.
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
- **TypeScript build info is tracked.** `frontend/tsconfig.app.tsbuildinfo` and
  `frontend/tsconfig.node.tsbuildinfo` are generated build artifacts currently
  tracked by Git; consider removing them from the repository and ignoring
  `*.tsbuildinfo`.

**Testing / tooling**
- **No frontend tests** beyond `build` / `lint` / `typecheck` (no unit or E2E).
- **Backend Ruff and mypy are advisory in CI for now.** They run in GitHub
  Actions, but existing lint/type debt prevents making them required without a
  dedicated cleanup milestone.
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

**Copilot persistence.**

Rationale: M29 established identity and M30 scopes user-created data. The next
step is to persist user-specific Copilot choices so the proactive features can
respect the user's decisions over time.

Suggested shape:
- Persist pinned/completed Copilot recommendations and daily briefing history.
- Feed persisted recommendation state back into Daily Briefing, Tasks, and
  Career Copilot without duplicating analytics logic.
- Keep organizations, teams, billing, and cloud sync out of scope.
