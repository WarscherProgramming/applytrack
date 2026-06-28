# ApplyTrack Deployment Preparation

This guide prepares ApplyTrack for a first cloud deployment without actually
deploying it.

Target providers:

- Frontend: Vercel
- Backend API: Render
- Database: Render Postgres or Neon
- File storage: local disk only for now

## Current Deployment Shape

```
Vercel frontend
  -> VITE_API_URL=https://<render-api>
  -> Render backend /api/v1/*
  -> Render Postgres or Neon
```

The frontend is a static Vite SPA. The backend is a FastAPI service. The
database is PostgreSQL. Uploaded resume and cover-letter files currently use
`STORAGE_BACKEND=local`, so they are not durable on an ephemeral Render service
unless a persistent disk is attached. S3/Azure/GCS storage is intentionally not
implemented in this milestone.

## Required Accounts

- GitHub account with access to this repository.
- Render account for the backend web service.
- Render Postgres or Neon account for PostgreSQL.
- Vercel account for the frontend.
- Optional: OpenAI account and API key.
- Optional: Google Cloud project for Gmail OAuth and future calendar OAuth.

## Production Environment Variables

### Backend: Render

Set these on the Render backend service:

| Variable | Required | Production value |
| --- | --- | --- |
| `DATABASE_URL` | yes | Managed Postgres URL, usually with `sslmode=require` for Neon |
| `SECRET_KEY` | yes | Strong random value, e.g. `openssl rand -hex 32` |
| `ENVIRONMENT` | yes | `production` |
| `LOG_LEVEL` | yes | `INFO` |
| `API_V1_PREFIX` | yes | `/api/v1` |
| `FRONTEND_URL` | yes | `https://<your-vercel-app>.vercel.app` |
| `BACKEND_CORS_ORIGINS` | yes | JSON array, e.g. `["https://<your-vercel-app>.vercel.app"]` |
| `ALGORITHM` | no | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | no | `7` |
| `AI_PROVIDER` | no | `mock` until OpenAI is ready; `openai` when configured |
| `OPENAI_API_KEY` | optional | OpenAI API key |
| `OPENAI_BASE_URL` | no | `https://api.openai.com/v1` |
| `AI_MODEL` | no | `gpt-4o-mini` |
| `AI_MAX_RETRIES` | no | `2` |
| `AI_REQUEST_TIMEOUT` | no | `30.0` |
| `GOOGLE_CLIENT_ID` | optional | Google OAuth client id |
| `GOOGLE_CLIENT_SECRET` | optional | Google OAuth client secret |
| `GOOGLE_REDIRECT_URI` | optional | `https://<render-api>/api/v1/gmail/callback` |
| `GOOGLE_CALENDAR_REDIRECT_URI` | optional | `https://<render-api>/api/v1/calendar-integration/google/callback` |
| `GMAIL_SIMULATION` | no | `true` until Google OAuth is configured |
| `STORAGE_BACKEND` | yes | `local` |
| `STORAGE_LOCAL_PATH` | yes | `storage` |
| `STORAGE_MAX_UPLOAD_BYTES` | yes | `10485760` |

Do not set `BACKEND_CORS_ORIGINS=*` in production. The backend rejects wildcard
CORS when `ENVIRONMENT=production`.

### Frontend: Vercel

Set this on the Vercel project:

| Variable | Required | Production value |
| --- | --- | --- |
| `VITE_API_URL` | yes | `https://<your-render-api>.onrender.com` |

`VITE_API_URL` must be the backend origin only, without `/api/v1`. The frontend
client appends `/api/v1`.

## Backend Deployment: Render

This repository includes [render.yaml](render.yaml) as a starting Render
blueprint.

Recommended Render settings:

- Service type: Web Service
- Runtime: Python
- Root directory: `backend`
- Build command: `pip install --upgrade pip && pip install -e .`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/health`
- Auto deploy: off for the first deploy, then enable once stable

Steps:

1. Create the PostgreSQL database in Render or Neon.
2. Create the Render web service from this repository or the `render.yaml`
   blueprint.
3. Add the backend environment variables listed above.
4. Deploy the service.
5. Run Alembic migrations against the production database.
6. Verify `/health` returns `{"status":"ok"}`.

## Frontend Deployment: Vercel

This repository includes [vercel.json](vercel.json) for a root-level Vercel
project.

Recommended Vercel settings:

- Framework preset: Vite
- Install command: `cd frontend && npm ci`
- Build command: `cd frontend && npm run build`
- Output directory: `frontend/dist`
- Environment variable: `VITE_API_URL=https://<your-render-api>.onrender.com`

`vercel.json` includes an SPA rewrite so refreshing nested React Router routes
serves `index.html`.

Steps:

1. Create a Vercel project from this repository.
2. Confirm the build settings above.
3. Set `VITE_API_URL` to the Render backend origin.
4. Deploy the frontend.
5. Copy the final Vercel URL.
6. Update Render `FRONTEND_URL` and `BACKEND_CORS_ORIGINS` with that exact URL.
7. Redeploy the backend after CORS changes.

## Database Setup And Migrations

ApplyTrack uses hand-written Alembic migrations. Do not auto-run migrations at
backend startup for the first deployment; it makes startup behavior harder to
reason about and can turn schema mistakes into repeated crash loops.

Run migrations manually after the backend service has the production
`DATABASE_URL`.

Options:

1. Render shell:

   ```bash
   cd backend
   alembic upgrade head
   ```

2. Local machine against the production database:

   ```bash
   cd backend
   DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require" \
   SECRET_KEY="temporary-local-migration-secret" \
   BACKEND_CORS_ORIGINS='["https://your-applytrack-app.vercel.app"]' \
   alembic upgrade head
   ```

Before running migrations, confirm the target database is empty or backed up.
For rollback planning, record the current migration with:

```bash
cd backend
alembic current
```

## OAuth Callback Setup

Gmail and calendar OAuth are optional for first deployment. The app still works
with `GMAIL_SIMULATION=true` and mock AI.

If enabling Google OAuth, configure these authorized redirect URIs in Google
Cloud Console:

- Gmail: `https://<your-render-api>.onrender.com/api/v1/gmail/callback`
- Google Calendar: `https://<your-render-api>.onrender.com/api/v1/calendar-integration/google/callback`

Then set:

- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI`
- `GOOGLE_CALENDAR_REDIRECT_URI`
- `GMAIL_SIMULATION=false`

Calendar provider writes are still simulation-mode foundations in this repo.
ICS export works without OAuth.

## File Storage Limitation

Documents currently use local storage:

- `STORAGE_BACKEND=local`
- `STORAGE_LOCAL_PATH=storage`

On a Render web service without a persistent disk, uploaded files can disappear
when the service restarts or redeploys. For a first demo deployment, either:

- Avoid relying on uploaded document durability, or
- Attach a Render persistent disk and point `STORAGE_LOCAL_PATH` at that mount.

Long-term production should implement cloud object storage before storing real
user resumes and cover letters.

## Smoke Test Checklist

Backend:

- `GET https://<render-api>/health` returns `{"status":"ok"}`.
- `POST /api/v1/auth/register` creates a user.
- `POST /api/v1/auth/login` returns access and refresh tokens.
- `GET /api/v1/auth/me` works with the access token.
- `GET /api/v1/settings/` returns the settings center.
- `GET /api/v1/companies/` returns only the current user's records.

Frontend:

- Vercel URL loads.
- Refreshing nested routes, such as `/settings`, does not 404.
- Register and login work.
- API calls go to the Render backend, not localhost.
- Logout returns to `/login`.

AI/Gmail/Calendar:

- With `AI_PROVIDER=mock`, AI-backed pages return simulated results.
- With `GMAIL_SIMULATION=true`, Gmail status/connect paths do not require real
  Google credentials.
- ICS export downloads a calendar file.

## Rollback Notes

Frontend rollback:

- Use Vercel's previous deployment promotion.
- If the backend URL changed, verify `VITE_API_URL` on the promoted deployment.

Backend rollback:

- Use Render's previous deploy rollback.
- If a rollback crosses a database migration boundary, check the Alembic
  revision first and decide whether a downgrade is safe.
- Do not run destructive downgrade migrations without a database backup.

Database rollback:

- Prefer restoring from a managed database backup.
- If using Alembic downgrade, test it against a copy first.

## Known Limitations For First Deployment

- No production object storage backend yet.
- Google Calendar external writes are simulation-mode foundations.
- Gmail real OAuth needs Google Cloud callback configuration.
- OpenAI is optional; mock AI remains the safe default.
- No organizations, teams, billing, or cloud sync.
- No deployment automation beyond CI validation and provider config templates.
