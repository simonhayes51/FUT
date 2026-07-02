# Deploying FC Edge on Railway

FC Edge is a **monorepo with two apps**, so Railway can't build it from the repo
root (that's the `Railpack could not determine how to build the app` error —
Railpack looks at the root and sees `apps/`, not a single app). Deploy each app
as its own service, each pointed at its own folder.

## Services

Create these in one Railway project:

| Service | Root Directory | Builder | Notes |
| --- | --- | --- | --- |
| **Postgres** | — | Railway plugin | provides `DATABASE_URL` |
| **Redis** | — | Railway plugin | provides `REDIS_URL` |
| **api** | `apps/api` | Dockerfile | FastAPI |
| **web** | `apps/web` | Dockerfile | Next.js |
| **worker** *(optional)* | `apps/api` | Dockerfile | `celery -A app.celery_app.celery worker` |
| **beat** *(optional)* | `apps/api` | Dockerfile | `celery -A app.celery_app.celery beat` |

For each app service, set **Settings → Root Directory** to the folder above.
With that set, Railway finds the `railway.json` / `Dockerfile` in the folder and
skips Railpack entirely.

## Environment variables

**api**
```
DATABASE_URL   = ${{Postgres.DATABASE_URL}}   # use postgresql+psycopg2:// scheme
REDIS_URL      = ${{Redis.REDIS_URL}}
CORS_ORIGINS   = https://<your-web-domain>    # the web service's public URL
ENABLE_TICKER  = true                         # or false if you run worker+beat
# OPENAI_API_KEY = sk-...                      # optional, enables the LLM Coach
```
> If `DATABASE_URL` comes through as `postgresql://…`, change the scheme to
> `postgresql+psycopg2://…` (SQLAlchemy needs the driver).

**web** — this one is a **build-time** variable (it is compiled into the bundle):
```
NEXT_PUBLIC_API_URL = https://<your-api-domain>/api/v1
```
This is the fix for the *"Can't reach the FC Edge API"* screen: the frontend
bakes this URL at build time, so it must point at the deployed API's public URL
(including the `/api/v1` suffix), not `localhost`. Change it and redeploy the web
service so the new value is baked in.

## Ports

Both Dockerfiles honour Railway's injected `$PORT` (API via
`uvicorn --port $PORT`, web via `next start -p $PORT`), so no port config is
needed.

## Data

The API seeds the demo dataset **only when the database is empty**
(`python -m app.seed --if-empty`), so redeploys won't wipe your data. To reseed
from scratch, drop the tables (or run `python -m app.seed` as a one-off) and
restart.

## Checklist when the web app can't reach the API

1. Is the **api** service deployed and healthy? Open `https://<api>/api/v1/health`.
2. Is `NEXT_PUBLIC_API_URL` set on **web** and did you **redeploy** after setting it?
3. Does the API's `CORS_ORIGINS` include the exact web domain (scheme + host)?
4. Does `NEXT_PUBLIC_API_URL` end with `/api/v1`?
