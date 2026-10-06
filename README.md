# RoutePulse — Logistics Tracking Automation Dashboard

RoutePulse is a demo logistics application that stores shipments, runs browser-based tracking, records tracking history, and presents operations data in a responsive dashboard. It demonstrates a practical separation between HTTP views, business services, Selenium adapters, and persistence.

> **Demo and security note:** the API currently has no user authentication. Anyone who can reach it can view, create, and track shipments. Keep it on a trusted local or private network; do not expose it publicly or store real customer data until authentication and authorization are added.

## Business problem

Operations teams often copy tracking numbers between spreadsheets and carrier sites. That workflow is slow, difficult to audit, and easy to get wrong. RoutePulse creates one shipment register and turns a manual carrier lookup into a traceable automation job with retry history and normalized events.

## Architecture

```mermaid
flowchart LR
  UI[Next.js dashboard] --> API[Django REST API]
  API --> SVC[Tracking service]
  SVC --> DB[(PostgreSQL)]
  SVC --> SEL[Selenium adapter]
  SEL --> MOCK[Demo Express site]
```

The Django views remain thin. `TrackingService` owns retries, transactions, job state, and event creation. `CarrierTracker` defines the carrier interface; `DemoExpressTracker` is the Selenium implementation. Tracking currently runs synchronously in the API request, so the request waits for Selenium and its retries to finish.

## Stack

- Python 3.12, Django 5, Django REST Framework
- PostgreSQL 16
- Selenium with Chromium, `WebDriverWait`, and expected conditions
- Next.js, React, TypeScript, Tailwind CSS
- Docker Compose
- pytest and Django API tests

## Quick start with Docker

```bash
cp .env.example .env
docker compose up --build
```

Open:

- Dashboard: <http://localhost:3000>
- API health: <http://localhost:8000/health/>
- Demo Express: <http://localhost:8081>

Create a shipment with `VN000001`, `VN000002`, or `VN000003`, then select **Track**.

## Deploy to Render (one click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/phatnguyen196-solverboiz/logistics-tracking-dashboard)

Or: Render dashboard → **New → Blueprint** → select this repository → **Apply**. No environment variables need to be entered.

[`render.yaml`](render.yaml) creates a free PostgreSQL database and one Docker web service built from [`Dockerfile.render`](Dockerfile.render):

- Next.js is the only public process. The browser calls same-origin `/api/*`, which [`frontend/app/api/[...path]/route.ts`](frontend/app/api/%5B...path%5D/route.ts) forwards to Django.
- Django + gunicorn listen on `127.0.0.1:8000` inside the container (not reachable from the internet; `/admin` is not exposed).
- Selenium opens the Demo Express page from disk (`file:///srv/mock-carrier/index.html`), so no extra service is needed.
- `DJANGO_SECRET_KEY` is generated and `DATABASE_URL` is wired by Render.

Free-plan notes: the service sleeps after ~15 minutes idle (first request takes ~1 minute), RAM is limited (one tracking run at a time is safest), and free databases expire after a limited period. The API still has no authentication — use demo data only.

## Local development

Backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Serve `mock-carrier/` on port 8081 (for example with Nginx or `python -m http.server 8081`). A local Chromium/Chrome installation is required for non-Docker Selenium runs.

## Environment variables

| Variable | Purpose | Default |
| --- | --- | --- |
| `DATABASE_URL` | PostgreSQL connection string | SQLite when omitted |
| `DJANGO_SECRET_KEY` | Django signing secret | development fallback |
| `DJANGO_DEBUG` | Debug mode | `true` |
| `ALLOWED_HOSTS` | Comma-separated hostnames | local hosts |
| `CORS_ALLOWED_ORIGINS` | Frontend origins | `http://localhost:3000` |
| `MOCK_CARRIER_URL` | Demo Express address used by Selenium | `http://localhost:8081` |
| `CHROME_BINARY` | Optional Chromium executable | Selenium discovery |
| `CHROMEDRIVER_PATH` | Optional local ChromeDriver executable | Selenium discovery |
| `NEXT_PUBLIC_API_URL` | Browser-facing API URL | `http://localhost:8000/api` |

Never commit production secrets. `.env` is ignored; `.env.example` contains only safe placeholders.

When setting `DJANGO_DEBUG=false`, configure a private `DJANGO_SECRET_KEY`, explicit `ALLOWED_HOSTS`, a persistent `DATABASE_URL`, and `CORS_ALLOWED_ORIGINS`. Django settings now stop startup when these production values are missing or unsafe. This does not add API authentication; keep the API on a private network.

## REST API

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/shipments/` | Create a shipment |
| GET | `/api/shipments/` | List shipments |
| GET | `/api/shipments/{id}/` | Retrieve a shipment |
| POST | `/api/shipments/{id}/track/` | Run the tracking workflow |
| GET | `/api/shipments/{id}/events/` | List tracking history |
| GET | `/api/jobs/{id}/` | Retrieve an automation job |

## Selenium workflow

1. Create an `AutomationJob` and mark it `RUNNING`.
2. Open the local Demo Express site.
3. Wait for the form, submit the tracking number, and wait for a result.
4. Parse and validate the status, location, and ISO timestamp.
5. Update the shipment and insert a tracking event in one database transaction.
6. Mark the job `SUCCESS`, or retry up to three times before marking it `FAILED`.
7. Close the browser in `finally` on every path.

No real carrier website is scraped and normal page synchronization does not use `time.sleep()`.

## Tests and quality checks

```bash
cd backend && pytest
cd ../frontend && npm run lint && npm run build
```

The tests cover creation, duplicate validation, listing, retrieval, API validation, successful and failed jobs, event creation, retries, and job retrieval. A database constraint prevents two simultaneous tracking jobs for one shipment, with a `409` response for the losing request. Selenium is replaced with deterministic test doubles in unit tests.

## Screenshots

- Dashboard — add screenshot after running the Compose stack.
- Shipment detail timeline — add screenshot after tracking `VN000001`.
- Demo Express response — add screenshot from port 8081.

## Future improvements

- Background jobs with Celery and Redis
- Carrier-specific rate limiting and circuit breakers
- Authentication and organization workspaces
- WebSocket job progress
- Metrics, tracing, and alerting
- Additional carrier adapters behind the same interface

See [docs/architecture.md](docs/architecture.md) for design decisions and failure behavior.
