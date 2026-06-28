# ApplyTrack Production Deployment Runbook

Current branch target: `chore/cloud-deployment`

This runbook deploys the current repository shape:

- Frontend: Vercel
- Backend: Render Web Service
- Database: Neon or Render Postgres
- File storage: current local-disk storage only

This is execution support, not a new architecture. Do not enable billing,
organizations, Kubernetes, Terraform, or cloud file storage during this run.

## 0. Preflight

Before deploying, confirm CI is green on the commit you plan to deploy.

Local verification commands:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml config --quiet
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend alembic upgrade head
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec backend python -m pytest -q
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec frontend npm run build
```

Important repository files:

- Backend config: `backend/app/core/config.py`
- Backend deployment blueprint: `render.yaml`
- Frontend deployment config: `vercel.json`
- Environment template: `.env.example`
- Deployment overview: `DEPLOYMENT.md`

## 1. Choose And Create The Database

Use either Neon or Render Postgres.

### Option A: Neon

1. Create a Neon project.
2. Create a production database, for example `applytrack`.
3. Copy the pooled or direct PostgreSQL connection string.
4. Ensure the URL uses SQLAlchemy-compatible syntax:

   ```text
   postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
   ```

   If Neon gives you a `postgres://...` URL, change the scheme to
   `postgresql://...`.

### Option B: Render Postgres

1. Create a Render PostgreSQL database.
2. Copy the internal database URL if the backend is also on Render.
3. Copy the external database URL only for local migration work.

Record this value as:

```text
DATABASE_URL=<managed-postgres-url>
```

## 2. Create The Render Backend

Use `render.yaml` as the reference. You can either create the service manually
or import the blueprint.

Recommended manual settings:

| Setting | Value |
| --- | --- |
| Service type | Web Service |
| Runtime | Python |
| Root directory | `backend` |
| Build command | `pip install --upgrade pip && pip install -e .` |
| Start command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Health check path | `/health` |
| Auto deploy | Off for first deploy |

Do not add a migration command to the start command for the first deployment.
Run Alembic manually after the service and database env vars are configured.

## 3. Set Render Backend Environment Variables

Required backend env vars:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require
SECRET_KEY=<strong-random-secret>
ENVIRONMENT=production
LOG_LEVEL=INFO
API_V1_PREFIX=/api/v1
FRONTEND_URL=https://<your-vercel-app>.vercel.app
BACKEND_CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]
AI_PROVIDER=mock
GMAIL_SIMULATION=true
STORAGE_BACKEND=local
STORAGE_LOCAL_PATH=storage
STORAGE_MAX_UPLOAD_BYTES=10485760
```

Recommended optional backend env vars:

```text
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
OPENAI_BASE_URL=https://api.openai.com/v1
AI_MODEL=gpt-4o-mini
AI_MAX_RETRIES=2
AI_REQUEST_TIMEOUT=30.0
```

Optional OpenAI env vars:

```text
AI_PROVIDER=openai
OPENAI_API_KEY=<openai-api-key>
```

Keep `AI_PROVIDER=mock` for the first production smoke test. Switch to OpenAI
only after the app is deployed and stable.

Optional Google OAuth env vars:

```text
GOOGLE_CLIENT_ID=<google-client-id>
GOOGLE_CLIENT_SECRET=<google-client-secret>
GOOGLE_REDIRECT_URI=https://<your-render-api>.onrender.com/api/v1/gmail/callback
GOOGLE_CALENDAR_REDIRECT_URI=https://<your-render-api>.onrender.com/api/v1/calendar-integration/google/callback
GMAIL_SIMULATION=false
```

For the first deployment, keep `GMAIL_SIMULATION=true`. Real Gmail OAuth and
calendar OAuth should be validated separately after basic production smoke tests.

Security notes:

- `BACKEND_CORS_ORIGINS` must be a JSON array string.
- Do not use `*` in production CORS. The backend rejects wildcard CORS when
  `ENVIRONMENT=production`.
- Generate `SECRET_KEY` with a strong random value, for example
  `openssl rand -hex 32`.

## 4. Deploy The Render Backend

1. Trigger the first Render deploy.
2. Wait for build and start to finish.
3. Open:

   ```text
   https://<your-render-api>.onrender.com/health
   ```

4. Expected response:

   ```json
   {"status":"ok"}
   ```

If `/docs` returns 404 in production, that is expected. `backend/app/main.py`
disables API docs when `ENVIRONMENT=production`.

## 5. Run Alembic Migrations

Run migrations only after the backend service has the production `DATABASE_URL`.

### Option A: Render Shell

In the Render backend shell:

```bash
cd backend
alembic current
alembic upgrade head
alembic current
```

### Option B: Local Machine Against Production DB

From the repo root:

```bash
cd backend
DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/DATABASE?sslmode=require" \
SECRET_KEY="temporary-local-migration-secret" \
FRONTEND_URL="https://<your-vercel-app>.vercel.app" \
BACKEND_CORS_ORIGINS='["https://<your-vercel-app>.vercel.app"]' \
ENVIRONMENT=production \
alembic upgrade head
```

Record the final revision shown by:

```bash
alembic current
```

Current expected head in this repository is revision `0016`.

## 6. Create The Vercel Frontend

Use `vercel.json` as the reference.

Recommended Vercel settings:

| Setting | Value |
| --- | --- |
| Framework preset | Vite |
| Install command | `cd frontend && npm ci` |
| Build command | `cd frontend && npm run build` |
| Output directory | `frontend/dist` |

Required frontend env var:

```text
VITE_API_URL=https://<your-render-api>.onrender.com
```

Do not include `/api/v1` in `VITE_API_URL`. The frontend client appends
`/api/v1` automatically.

Deploy the frontend and copy the final Vercel URL.

## 7. Update Backend After Vercel URL Is Known

Once Vercel gives you the production frontend URL, update the Render backend:

```text
FRONTEND_URL=https://<your-vercel-app>.vercel.app
BACKEND_CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]
```

Redeploy the Render backend after changing these values.

If you also use a custom domain, include both exact origins:

```text
BACKEND_CORS_ORIGINS=["https://<your-vercel-app>.vercel.app","https://app.yourdomain.com"]
```

## 8. OAuth Callback URLs

OAuth is optional for the first production deployment.

Google Cloud authorized redirect URIs:

```text
https://<your-render-api>.onrender.com/api/v1/gmail/callback
https://<your-render-api>.onrender.com/api/v1/calendar-integration/google/callback
```

Matching Render env vars:

```text
GOOGLE_REDIRECT_URI=https://<your-render-api>.onrender.com/api/v1/gmail/callback
GOOGLE_CALENDAR_REDIRECT_URI=https://<your-render-api>.onrender.com/api/v1/calendar-integration/google/callback
```

First-deploy recommendation:

- Keep `GMAIL_SIMULATION=true`.
- Validate registration, login, core CRUD, settings, AI mock responses, and ICS
  export first.
- Enable real Google OAuth only after the baseline app is stable.

Current caveat:

- Google Calendar external writes are still simulation-mode foundations.
- Browser OAuth callback behavior should be tested carefully before relying on
  real Gmail in production.

## 9. Production Smoke Test Checklist

Backend health:

- Open `https://<your-render-api>.onrender.com/health`.
- Confirm `{"status":"ok"}`.

Frontend routing:

- Open `https://<your-vercel-app>.vercel.app`.
- Refresh `/login`.
- Refresh `/register`.
- Refresh `/settings`.
- Refresh `/tasks`.
- None of these should produce a Vercel 404 because `vercel.json` rewrites to
  `index.html`.

Auth:

- Register a new user.
- Log out.
- Log back in.
- Open Settings.
- Update full name or timezone.
- Log out again.

API/CORS:

- In browser devtools, confirm requests go to:

  ```text
  https://<your-render-api>.onrender.com/api/v1/*
  ```

- Confirm requests are not going to `localhost`.
- Confirm there are no CORS errors.

Core app:

- Create a company.
- Create an application for that company.
- Create a recruiter.
- Create a follow-up.
- Open dashboard or Career Copilot.

AI/Gmail/Calendar:

- With `AI_PROVIDER=mock`, AI pages should return simulated outputs.
- With `GMAIL_SIMULATION=true`, Gmail connect should not require real Google
  credentials.
- Download ICS export from calendar integration.

Documents:

- Upload a small test resume only if you accept the current local-storage
  limitation.
- Do not rely on uploaded documents surviving Render restarts unless a
  persistent disk is attached.

## 10. Rollback Checklist

Frontend rollback:

1. In Vercel, promote the previous successful deployment.
2. Confirm `VITE_API_URL` still points to the active Render backend.
3. Smoke test login and `/settings`.

Backend rollback:

1. In Render, roll back to the previous successful deploy.
2. Confirm `/health`.
3. Confirm the rolled-back backend is compatible with the current database
   schema.
4. If the rollback crosses an Alembic migration boundary, prefer restoring a
   database backup over ad hoc downgrade commands.

Database rollback:

1. Stop writes if possible.
2. Restore from managed database backup.
3. Redeploy backend/frontend versions that match the restored schema.
4. Run `alembic current` and record the restored revision.

Environment rollback:

1. Revert recent Render env var changes.
2. Revert recent Vercel env var changes.
3. Redeploy affected service.

## 11. Common Errors And Fixes

### Backend fails on startup: missing `DATABASE_URL` or `SECRET_KEY`

Fix:

- Set both env vars in Render.
- Redeploy the backend.

### Backend fails on startup: wildcard CORS rejected

Cause:

- `ENVIRONMENT=production` and `BACKEND_CORS_ORIGINS` contains `*`.

Fix:

```text
BACKEND_CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]
```

### Frontend calls `localhost:8000` in production

Cause:

- Vercel `VITE_API_URL` is missing or set to a local value.

Fix:

```text
VITE_API_URL=https://<your-render-api>.onrender.com
```

Then redeploy Vercel. Vite env vars are baked at build time.

### Frontend API calls 404 with duplicated `/api/v1`

Cause:

- `VITE_API_URL` includes `/api/v1`.

Fix:

```text
VITE_API_URL=https://<your-render-api>.onrender.com
```

The frontend appends `/api/v1`.

### CORS error in browser

Fix:

- Confirm `BACKEND_CORS_ORIGINS` is valid JSON.
- Confirm it contains the exact Vercel origin, including `https://`.
- Redeploy Render after env var changes.

### Login works locally but not in production

Checks:

- `SECRET_KEY` is set and stable on Render.
- Backend deploy did not regenerate `SECRET_KEY` after users were created.
- Browser requests target the Render backend.
- Render logs do not show database connection errors.

### Alembic cannot connect to Neon

Fix:

- Ensure the URL starts with `postgresql://`.
- Include `sslmode=require` if Neon requires it.
- Confirm the database password is URL-encoded if it contains special
  characters.

### Tables do not exist

Cause:

- Migrations were not run.

Fix:

```bash
cd backend
alembic upgrade head
```

### `/docs` is missing in production

This is expected. Production disables Swagger/OpenAPI routes to reduce exposed
surface area. Use `/health` for health checks.

### Uploaded resumes disappear after redeploy

Cause:

- Current storage backend is local disk.
- Render service disk may be ephemeral without an attached persistent disk.

Fix:

- Do not rely on document durability for first deployment, or attach a Render
  persistent disk and set `STORAGE_LOCAL_PATH` to that mount.
- Long term, implement object storage in a future milestone.

### Gmail real OAuth does not complete

First-deploy fix:

- Keep `GMAIL_SIMULATION=true`.

When enabling real OAuth:

- Confirm Google Cloud authorized redirect URI exactly matches
  `GOOGLE_REDIRECT_URI`.
- Confirm `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set on Render.
- Confirm `FRONTEND_URL` points to the Vercel app.
- Check Render logs for callback errors.

### Calendar connect appears simulated

This is expected. Calendar integration currently provides provider foundations
and ICS export. Real provider writes are not production-ready in this milestone.

## 12. First Deployment Order

Use this sequence to avoid circular frontend/backend URL confusion:

1. Create database and copy `DATABASE_URL`.
2. Create Render backend with placeholder:

   ```text
   FRONTEND_URL=https://placeholder.invalid
   BACKEND_CORS_ORIGINS=["https://placeholder.invalid"]
   ```

3. Deploy backend.
4. Run Alembic migrations.
5. Confirm backend `/health`.
6. Create Vercel frontend with:

   ```text
   VITE_API_URL=https://<your-render-api>.onrender.com
   ```

7. Deploy frontend.
8. Copy final Vercel URL.
9. Update Render:

   ```text
   FRONTEND_URL=https://<your-vercel-app>.vercel.app
   BACKEND_CORS_ORIGINS=["https://<your-vercel-app>.vercel.app"]
   ```

10. Redeploy backend.
11. Run the smoke test checklist.
