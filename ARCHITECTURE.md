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
                                                ├─ Gmail (simulation | Google)
                                                └─ Calendars (ICS | simulated Google/Outlook)
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
  (`BaseRepository[Model]` with global CRUD helpers plus
  `get_for_user/get_or_raise_for_user` for owned records) and adds query methods
  (e.g. `list_paginated`). **Never calls `commit()`** —
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
  `ownership`, plus the `documents/` and `storage/` subsystems (below).

### Registered features

`auth`, `users`, `settings`, `companies`, `applications`, `recruiters`, `interviews`,
`followups`, `gmail`, `resumes`, `cover_letters`, `resume_match`,
`cover_letter_ai`, `interview_ai`, `career_intelligence`, `career_copilot`,
`job_intelligence`, `opportunity_discovery`, `daily_briefing`,
`calendar_integration`, `tasks`.

> **Scaffold stubs (not implemented):** `features/{analytics, attachments,
> emails, follow_ups, notifications}`, `integrations/{gmail, google_calendar}`,
> `ai/{agents, prompts, tools}`. See PROJECT_STATUS section 5. Note `follow_ups` (stub)
> is distinct from `followups` (real).

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
- **`services/api-client.ts`** - central Axios instance. Base URL is
  `VITE_API_URL` + `/api/v1` in dev, or relative `/api/v1` in prod (nginx
  proxies). It attaches JWT access tokens from `auth-tokens.ts`, refreshes once
  on eligible 401 responses via `/auth/refresh`, retries the original request,
  and normalizes error `status`.
- **`features/auth/`** - login/register API wrappers, token types, AuthProvider,
  protected-route wrapper, and token lifecycle helpers.
- **`features/settings/`** - typed settings-center API wrappers and mutation
  hooks for account preferences, security actions, sessions, and JSON export.
- **`components/ui/`** - shadcn/ui primitives (Radix + Tailwind + CVA).
- **`components/common/`, `components/layout/`** - shared composite components
  and the app shell (sidebar, topbar).
- **`pages/`** - one component per route.
- **`routes/index.tsx`** - `createBrowserRouter`; **every page is `React.lazy`**
  for code splitting, with a single `<Suspense>` boundary around `<Outlet />` in
  the layout. Public auth routes live at `/login` and `/register`; the app shell
  is wrapped by `ProtectedRoute`. **Add new routes here.**
- **`app/navigation.ts`** - sidebar nav items. **Add new nav entries here.**
- **`app/providers.tsx`** - QueryClient, AuthProvider, theme, tooltip, and toast
  providers.

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
  `0001`…`0016`, each with explicit `upgrade()`/`downgrade()` and a linear
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
`ai_usage_records`, `resume_match_analyses`, `interview_prep_packages`,
`notifications`, `calendar_connections`, `calendar_sync_events`, `tasks`,
`users`, `auth_refresh_tokens`, `user_settings`.

`career_intelligence`, `career_copilot`, `job_intelligence`, and
`opportunity_discovery` are table-free derived features. They compute analytics,
briefing context, job-market signals, and external opportunity scores from
existing CRM, Gmail, document, interview, follow-up, AI-history, and public
provider data. Opportunity Discovery only persists when the user explicitly
saves a posting into Companies + Applications.

`daily_briefing` is mixed: the briefing response is derived from existing
services, while notification state is persisted in `notifications` so read,
pinned, and dismissed state survives refreshes.

`calendar_integration` persists connection state and sync mappings only. The
calendar payloads are derived from existing interviews and follow-ups; external
event IDs and event hashes prevent duplicate events and allow updates/deletes.

`tasks` persists actionable work. Tasks may be manual or generated from existing
ApplyTrack signals; generated tasks use a stable `source_key` so refreshes
update or skip existing items instead of duplicating them.

`auth` and `users` persist identity and session state. `users` stores the account
record and hashed password; `auth_refresh_tokens` stores hashed refresh tokens
with expiry/revocation metadata.

`settings` persists per-user account preferences in `user_settings`. Security
actions reuse the Authentication refresh-token repository and the shared
`core/security.py` helpers instead of duplicating auth logic. Data export is
scoped to the current user and serializes user-owned ApplyTrack records as JSON
without exposing `user_id` or encrypted provider tokens.

### User data ownership

User-created domain tables use `app/shared/ownership.py`'s `UserOwnedMixin`.
Owned rows have a non-null `user_id` FK to `users.id`, indexed for query
scoping. Current owned tables include companies, applications, recruiters,
interviews, follow-ups, resumes, cover letters, Gmail accounts/emails,
notifications, calendar connections/sync mappings, tasks, Resume Match history,
Interview Prep history, and AI usage records where applicable.

Feature routers that expose existing domain data depend on `CurrentUser`.
Services are constructed with `current_user.id`, create paths stamp that id, and
repositories scope list/get/update/delete operations by the same id. Direct
cross-user access is intentionally indistinguishable from a missing record and
returns 404. Per-user uniqueness is enforced for natural keys such as company
name, recruiter email, Gmail account email, notification dedupe key, calendar
provider connection, calendar sync item, and generated task source key.

Migration `0015_add_user_ownership.py` safely backfills existing local/demo rows
to the oldest user, or creates an inactive legacy owner when owned rows exist
before any users. It keeps AI usage nullable so historical usage records can
survive user deletion.

Migration `0016_create_user_settings.py` creates one settings row per user and
backfills existing users with defaults. Settings stay separate from `users` so
identity/security concerns remain reusable and future preferences can grow
without widening the authentication model.

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
- **career_intelligence** has **no table** — deterministic analytics are computed
  first, then the AI platform interprets those computed facts into
  recommendations. If AI is unavailable, the analytics response still succeeds
  with a clear recommendation caveat.
- **career_copilot** has **no table** — it orchestrates Career Intelligence plus
  Gmail, interviews, follow-ups, and the application pipeline into a daily
  briefing. AI only narrates computed facts; deterministic priorities are always
  returned.
- **job_intelligence** has **no table** — it extracts and normalizes structured
  technology signals from saved Resume Match and Interview Prep job
  descriptions, compares them against resume skills and Resume Match history,
  and lets AI interpret those deterministic analytics.
- **opportunity_discovery** has **no table** — it fetches public board/feed
  postings through provider adapters, normalizes them, scores them
  deterministically, and uses AI only to explain the computed score. Saving an
  opportunity writes through the existing Companies and Applications features.
- **daily_briefing** has one table (`notifications`) for user-facing notification
  state. The daily briefing itself is deterministic orchestration over Career
  Copilot, Career Intelligence, Job Intelligence, Gmail, interviews,
  follow-ups, and Opportunity Discovery-sourced applications; AI only narrates
  the computed facts.
- **calendar_integration** does not use AI. It normalizes existing interviews
  and follow-ups into calendar event payloads, then sends them through provider
  adapters. ICS export is read-only and works without OAuth; Google/Outlook are
  simulation-mode provider foundations until real token exchange/API writes are
  added.
- **tasks** persists manual and generated work items. Core task logic is
  deterministic; task generation reuses Daily Briefing outputs, overdue
  follow-ups, upcoming interviews, and unread recruiter Gmail messages. AI may
  influence tasks only indirectly through Daily Briefing recommendations.
- AI clients are **injectable** (`ai_client=...`) so tests pass a deterministic
  mock; the API path is exercised by overriding the router's `_get_service`
  dependency.

---

## Career Intelligence architecture (`backend/app/features/career_intelligence/`)

Career Intelligence is a read-only analytics feature:

- **`repository.py`** gathers existing records only; it never persists anything.
- **`service.py`** owns deterministic calculations: application conversion
  rates, company/industry/location responsiveness, document-version performance,
  skill extraction from stored AI job descriptions, interview topic aggregation,
  and optional period comparisons.
- **AI recommendations** are a final interpretation step over the computed JSON
  facts using the existing AI platform and the central `career_intelligence.v1`
  prompt. AI does not calculate metrics and does not block the dashboard.
- **`router.py`** exposes `GET /api/v1/career-intelligence/` with date and
  comparison filters.

The frontend page (`/career-intelligence`) uses a feature-local typed API/hook,
Recharts visualizations, client-side JSON export, refresh, date filtering, and
comparison-period controls.

---

## Career Copilot architecture (`backend/app/features/career_copilot/`)

Career Copilot is a read-only orchestration feature:

- **`repository.py`** gathers existing applications, companies, follow-ups,
  upcoming interviews, and recent Gmail activity.
- **`service.py`** calls `CareerIntelligenceService` for analytics, then adds
  time-sensitive deterministic aggregation: today's metrics, ranked priorities,
  upcoming deadlines, recent email activity, interview reminders, follow-up
  reminders, skill focus, and resume recommendations.
- **AI narrative** is a final step over the computed briefing JSON using the
  existing AI platform and central `career_copilot.v1` prompt. If AI fails, the
  endpoint still returns deterministic priorities and fallback copy.
- **`router.py`** exposes `GET /api/v1/career-copilot/daily`.

The frontend Career Copilot page is the default route (`/`). It uses a
feature-local typed API/hook, refresh/export actions, client-side pin/complete
state for recommendations, priority cards, timeline, Gmail activity, upcoming
interviews, quick actions, and empty/loading/error states. The previous overview
dashboard remains available at `/dashboard`.

---

## Job Intelligence architecture (`backend/app/features/job_intelligence/`)

Job Intelligence is a reusable read-only analytics engine for saved job
descriptions:

- **Extraction** identifies known programming languages, frameworks, cloud
  platforms, databases, DevOps tools, concepts, and soft skills from every saved
  job description.
- **Normalization** maps aliases such as `k8s`, `postgres`, and `google cloud`
  to canonical skill names so downstream analytics use one vocabulary.
- **Analytics** computes frequency, percentage, trend over time, and industry /
  company / role distributions for each signal. It also extracts resume skills
  through the existing Resume Library + Resume Match text extraction path and
  calculates deterministic missing-skill gaps, including Resume Match gap
  counts when available.
- **AI interpretation** is a final step over computed JSON facts using the
  existing AI platform and central `job_intelligence.v1` prompt. If AI fails,
  the endpoint still returns the deterministic report plus fallback guidance.
- **`router.py`** exposes `GET /api/v1/job-intelligence/` with date, industry,
  company, and role filters.

The frontend page (`/job-intelligence`) uses a feature-local typed API/hook,
Recharts visualizations, a CSS heatmap, JSON export, refresh, filters, and
loading/error/empty states.

---

## Opportunity Discovery architecture (`backend/app/features/opportunity_discovery/`)

Opportunity Discovery turns external public job sources into scored pipeline
candidates without automatic applications:

- **Provider abstraction**: `JobProvider.fetch(ProviderFetchRequest)` returns
  normalized `NormalizedJobPosting` objects. Greenhouse, Lever, Ashby, and RSS
  adapters use documented public JSON/RSS endpoints only; they do not scrape
  restricted pages.
- **Normalization**: provider adapters standardize company, title, location,
  salary, employment type, work mode, URL, posted date, description, and skills.
  Skills are extracted through the Job Intelligence taxonomy so future providers
  plug into the same vocabulary.
- **Scoring**: `OpportunityScoringEngine` is deterministic and separate from
  providers. It scores resume skill overlap, missing skills, preferred
  location/job type/industry, and historical response rates from tracked
  applications and companies. Resume and cover-letter recommendations come from
  existing document versions.
- **AI explanation**: the final step renders `opportunity_discovery.v1` with the
  normalized posting and deterministic score. AI explains the score only; it
  does not fetch jobs, calculate metrics, or fabricate values. If AI fails, the
  API returns fallback deterministic rationale.
- **Save flow**: `POST /api/v1/opportunity-discovery/save` creates/reuses the
  company and creates a draft application with the posting URL, source, salary,
  location, and recommended document links. It does not submit applications.

The frontend page (`/opportunity-discovery`) exposes source inputs, provider /
remote / location / salary / technology filters, scored job cards, comparison,
quick resume-match details, one-click add to Applications, and Recharts
summaries for technologies, industries, and locations.

---

## Daily Briefing architecture (`backend/app/features/daily_briefing/`)

Daily Briefing is the proactive notification layer:

- **Deterministic briefing data** comes first. `service.py` reuses
  `CareerCopilotService`, `CareerIntelligenceService`, and
  `JobIntelligenceService`, then adds due/overdue follow-ups, upcoming
  interviews, recent recruiting Gmail messages, recent Opportunity
  Discovery-sourced applications, resume performance changes, skill trend
  updates, and prioritized actions.
- **Notifications** are persisted in `notifications`. Each generated alert has a
  stable `dedupe_key` so refreshing the briefing updates active reminders
  without creating duplicates. Read/unread, pinned/unpinned, and dismissed state
  are mutable through the notification API.
- **AI narrative** is a final interpretation step over computed briefing JSON
  using `daily_briefing.v1`. If AI fails, the endpoint still returns the
  deterministic briefing and fallback recommendations.
- **Routes:** `GET /api/v1/daily-briefing/`,
  `POST /api/v1/daily-briefing/refresh`,
  `GET /api/v1/daily-briefing/notifications`, and
  `PATCH /api/v1/daily-briefing/notifications/{id}`.

The frontend page (`/daily-briefing`) shows the morning briefing, priority
cards, follow-up/interview timeline, opportunity highlights, skill updates,
resume performance notes, unread count, pinned notifications, and notification
actions for mark read, pin, and dismiss. It also supports refresh and JSON
export.

---

## Calendar Integration architecture (`backend/app/features/calendar_integration/`)

Calendar Integration syncs ApplyTrack schedule data outward without changing
interview or follow-up ownership rules:

- **Provider abstraction:** `providers/base.py` defines the calendar adapter
  surface. Google and Outlook adapters currently provide OAuth/connect
  foundations plus deterministic simulation-mode upsert/delete behavior. No
  provider-specific code lives in the service.
- **Normalization:** `service.py` converts interviews and pending follow-ups
  into `CalendarEventPayload` objects. Interviews use scheduled time/duration;
  follow-ups become 30-minute reminders at 9 AM UTC on the due date.
- **Idempotency:** `calendar_sync_events` stores `(provider, item_type,
  item_id)` uniqueness, the external event ID, and a SHA-256 hash of the
  normalized payload. Unchanged payloads are skipped; changed payloads update
  the existing external event ID.
- **Delete/cancel handling:** inactive source items (cancelled/no-show
  interviews, completed/skipped follow-ups, or deleted source rows) mark their
  sync mapping deleted and call the provider delete hook.
- **ICS fallback:** `providers/ics.py` exports active calendar payloads as a
  VCALENDAR response and requires no OAuth connection.
- **Routes:** `GET /api/v1/calendar-integration/status`,
  `POST /api/v1/calendar-integration/connect/{provider}`,
  `GET /api/v1/calendar-integration/{provider}/callback`,
  `POST /api/v1/calendar-integration/disconnect/{provider}`,
  `POST /api/v1/calendar-integration/sync`,
  `POST /api/v1/calendar-integration/interviews/{id}/sync`,
  `POST /api/v1/calendar-integration/followups/{id}/sync`, and
  `GET /api/v1/calendar-integration/ics`.

The frontend exposes a Calendar Integration settings page at
`/settings/calendar`, also embeds the same settings card on `/settings`, and
adds a Google sync action to the interview detail dialog. Follow-ups currently
have only the placeholder page, so they are synced through manual/global sync
until a real follow-up detail view exists.

---

## Task System architecture (`backend/app/features/tasks/`)

Tasks convert insights into explicit work without changing the source features:

- **Persistent workflow:** `tasks` stores title, description, status, priority,
  due date, completion timestamp, source, optional links to applications,
  companies, recruiters, interviews, follow-ups, and an optional
  Opportunity Discovery posting id.
- **Statuses:** `backlog`, `today`, `in_progress`, `completed`, `dismissed`.
  Completing a task stamps `completed_at`; reopening clears it.
- **Generation:** `TaskService` creates tasks from Daily Briefing
  recommendations, overdue follow-ups, upcoming interviews, and unread
  recruiter Gmail messages. It does not duplicate Daily Briefing, follow-up,
  interview, or Gmail business logic.
- **Dedupe:** generated tasks carry a stable `source_key` such as
  `followup:<id>` or `interview:<id>`. Existing active generated tasks are
  refreshed; completed/dismissed generated tasks are skipped so user decisions
  are respected.
- **AI boundary:** no AI provider code appears in Tasks. AI can influence a task
  only through existing Daily Briefing recommendations.
- **Routes:** `GET/POST /api/v1/tasks/`, `GET/PATCH/DELETE /api/v1/tasks/{id}`,
  `POST /api/v1/tasks/{id}/complete`, `POST /api/v1/tasks/{id}/dismiss`, and
  generation routes under `/api/v1/tasks/generate/*`.

The frontend page (`/tasks`) provides Today, Backlog, In Progress, and
Completed views, priority/source filters, task cards, create/edit dialog,
complete/dismiss/delete actions, generation from ApplyTrack activity, and
loading/error/empty states.

---

## Authentication architecture (`backend/app/features/auth/`, `backend/app/features/users/`)

Authentication establishes identity and supplies the dependency used by
user-owned domain features:

- **Users feature:** owns the `users` table, account profile schema, email
  uniqueness, active-user state, and `PATCH /api/v1/users/me`.
- **Auth feature:** owns registration, login, refresh, logout, current-user
  lookup, and the shared `get_current_user` dependency.
- **Password storage:** `core/security.py` is the only password/JWT helper. New
  passwords are hashed with `pbkdf2_sha256`; bcrypt remains configured for
  legacy verification compatibility. Plain-text passwords are never stored.
- **Access tokens:** JWT access tokens use the user UUID as `sub` and expire via
  `ACCESS_TOKEN_EXPIRE_MINUTES`.
- **Refresh tokens:** raw refresh tokens are returned only to the client; the DB
  stores a SHA-256 hash in `auth_refresh_tokens`. Refresh rotates the token and
  revokes the previous row. Logout revokes either the submitted token or all
  active tokens for the current user.
- **Protected dependency:** `auth/dependencies.py` uses HTTP bearer auth,
  decodes the access token, rejects inactive/missing users, and exposes
  `CurrentUser` for protected routes.
- **Scope boundary:** M30 applies `CurrentUser` to existing domain routers and
  binds services to `current_user.id`, so authenticated users only see and
  mutate their own records. Organizations, teams, shared records, and role-based
  access remain out of scope.

Frontend authentication lives in `frontend/src/features/auth/`,
`frontend/src/services/auth-tokens.ts`, and the Axios interceptors in
`frontend/src/services/api-client.ts`. Tokens are kept client-side, the app shell
redirects unauthenticated users to `/login`, and account settings update the
current user through `/users/me`.

---

## Settings & Security architecture (`backend/app/features/settings/`)

Settings is an account center layered on top of Authentication without owning
login, registration, or token creation:

- **Account settings:** email/full-name updates delegate to `UserService`, while
  timezone and notification preferences live in `user_settings`.
- **Preferences:** theme, default dashboard page, default notification behavior,
  preferred calendar provider, and preferred AI provider are stored per user.
  Preferred AI provider validation is configuration-aware; `auto` and `mock`
  are always valid, while `openai` is only offered when configured.
- **Security:** password changes verify the current password, run the shared
  strong-password validator in `core/security.py`, update the existing user
  password hash, and revoke old refresh-token sessions.
- **Sessions:** session listing and sign-out actions operate on
  `auth_refresh_tokens` through the auth repository. The raw refresh token is
  accepted only from the client and is immediately hashed before lookup.
- **Data export:** export gathers scoped user-owned records from existing
  models, converts UUID/datetime values to JSON-safe strings, omits `user_id`,
  and excludes encrypted OAuth/provider tokens.
- **Routes:** `GET /api/v1/settings/`, `PATCH /api/v1/settings/account`,
  `PATCH /api/v1/settings/preferences`,
  `PATCH /api/v1/settings/notifications`,
  `POST /api/v1/settings/security/change-password`, session actions under
  `/api/v1/settings/sessions`, and `GET /api/v1/settings/export`.

The frontend settings page lives at `/settings` and uses
`frontend/src/features/settings/` for API calls and TanStack Query mutations.
It presents account, security, preferences, notifications, calendar, AI, Gmail,
and export sections with loading/error states, success toasts, unsaved-change
indicators, and confirmation dialogs for session sign-out actions.

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

`features/resumes/` and `features/cover_letters/` are thin: a user-owned
concrete model
(`Resume` / `CoverLetter`) on `DocumentBase`, a repository, a `DocumentService`
subclass (with `storage_prefix`), shared schemas, and a router from the factory.
Versions are grouped by `(user_id, name)`; uploading the same name creates the
next version for that user only.

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
  start clean. The `client` fixture overrides `get_db` to share that session and
  sends a JWT for a generated active test user by default; use
  `anonymous_client` for unauthenticated cases.
- **AI testing:** the `MockProvider` and injectable `AIClient` make AI
  deterministic; the API path is tested by overriding the router's
  `_get_service`. `OpenAIProvider` is tested with an `httpx.MockTransport`.
  **No test makes a real external API call** (AI or Gmail).
- **Current status:** 455 passing.
- **Frontend:** no unit/E2E tests yet; quality gates are `npm run build`
  (includes `tsc -b`), `npm run lint`, `npm run typecheck`.

See [CONTRIBUTING.md](CONTRIBUTING.md) for exact commands.
