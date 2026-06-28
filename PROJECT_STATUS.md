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
- Database schema: Alembic revisions `0001` → `0012`
- Backend tests: **436 passing** on the last full committed run; M27 adds 4
  calendar integration tests pending Docker-backed execution in this workspace.
- Latest **committed** milestone: **M26 — Daily Briefing & Notifications** (`f5c31bd`)
- Current `HEAD` includes Daily Briefing & Notifications: proactive briefing,
  notification records, notification center UI, and the `notifications`
  migration.
- **M27 — Calendar Integration is implemented in the working tree but not yet
  committed.** It adds the `calendar_integration` feature, Google/Outlook
  provider foundations, ICS export, calendar sync settings UI, interview sync
  controls, and the `calendar_connections` / `calendar_sync_events` migration.

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
| **M22** | **Career Intelligence Dashboard** | **committed** |
| **M23** | **AI Career Copilot** | **committed** |
| **M24** | **AI Job Intelligence Engine** | **committed** |
| **M25** | **Opportunity Discovery Engine** | **committed** |
| **M26** | **Daily Briefing & Notifications** | **committed** |
| **M27** | **Calendar Integration** | **in working tree (uncommitted)** |

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
- **Career Intelligence** (M22) — search-wide analytics across applications,
  companies, Gmail, documents, interviews, and AI history; deterministic metrics
  work without AI, while AI recommendations interpret computed facts only.
- **AI Career Copilot** (M23) — proactive daily briefing, ranked priorities,
  upcoming deadline timeline, skill/resume/interview/follow-up reminders, and
  AI narrative over deterministic facts. It reuses Career Intelligence and
  existing CRM/Gmail/interview/follow-up data.
- **AI Job Intelligence Engine** (M24) — structured extraction, normalization,
  trend analysis, market distributions, deterministic resume-skill gaps, and AI
  interpretation over saved job descriptions from Resume Match and Interview
  Prep. It exposes reusable analytics for future recommendations.
- **Opportunity Discovery Engine** (M25) — public provider adapters for
  Greenhouse, Lever, Ashby, and RSS; normalized job postings; deterministic
  scoring against resumes, preferences, and response history; AI explanations
  over scores; and one-click save into Companies + Applications.
- **Daily Briefing & Notifications** (M26) — proactive morning briefing,
  prioritized action list, follow-up/interview/Gmail/opportunity/AI insight
  notifications with unread/read, pinned/unpinned, dismissed, priority, and
  category state.
- **Calendar Integration** (M27) — external calendar sync foundation for
  interviews and follow-up reminders. Google and Outlook are provider adapters
  running in deterministic simulation mode until real OAuth token exchange/API
  writes are enabled; ICS export works without OAuth. Sync is idempotent via
  stored external event IDs and event hashes.
- **AI usage tracking** — every AI call is recorded in `ai_usage_records`
  (provider, model, tokens, estimated cost, latency, feature).

## 4. Current roadmap

Short term (recommended order):
1. **Review and commit M27** (Calendar Integration).
2. **M28 — Authentication & Multi-User Foundation** — _the biggest gap_ (see
   §5). The app is
   currently single-user with no auth; the Settings page explicitly says
   "Authentication arrives in a later milestone."
3. **Copilot persistence** — persist pinned/completed recommendations and daily
   briefing history once authentication/user scoping exists.

Planned/aspirational (per `PROJECT.md` and existing scaffold stubs):
- Real calendar OAuth token exchange and external provider writes beyond the
  M27 simulation-mode foundations.
- Attachments and richer analytics (feature stubs exist).
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
  are untested. Opportunity Discovery provider adapters are covered with mocked
  payloads but have not been validated against live boards/feed URLs. Calendar
  Integration has Google/Outlook provider foundations and deterministic sync
  simulation, but no real token exchange or external calendar write calls yet.
- **AI "streaming" is simulated.** Generation is a single synchronous request;
  the UI shows an animated progress indicator, not true token streaming.
- **Storage is local-disk only.** The `FileStorage` abstraction is designed for
  cloud backends (S3/Azure/Drive) but only `LocalFileStorage` is implemented.

**Cleanup**
- **Empty scaffold directories** (created during early scaffolding, never
  implemented): `backend/app/features/{analytics, attachments, auth, emails,
  follow_ups, notifications, users}`, `backend/app/integrations/{gmail,
  google_calendar}`, `backend/app/ai/{agents, prompts, tools}`. Either implement
  or remove. Note that real notification records now live under
  `features/daily_briefing`, so the old `features/notifications` stub remains
  stale.
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

**M28 — Authentication & Multi-User Foundation.**

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

Before starting M28, consider tackling the §5 cleanup items (delete stub dirs,
complete `.env.example`, and stop tracking generated TypeScript build info).
