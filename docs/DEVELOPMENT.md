# DEVELOPMENT

## Local Prerequisites

- Python 3.11 (recommended for backend parity with CI).
- Node.js 20+ for frontend and CI parity.
- Docker and Docker Compose for full-stack runtime.

## Backend Setup

```bash
cd backend
python -m venv .venv311
source .venv311/bin/activate
pip install -r requirements-dev.txt
```

Run backend locally:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend Setup

```bash
cd frontend
npm install
npm start
```

## Testing

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test -- --watchAll=false
```

## Quality Gates

- Backend test coverage threshold: 80%.
- Security baseline gate (non-local hardening):

```bash
cd backend
python scripts/verify_runtime_security.py --strict
```

CI uses `--require-non-local` with `ENVIRONMENT=production`.

- Startup readiness gate:

```bash
cd backend
python scripts/check_startup_readiness.py --strict --include-dependencies
```

- Endpoint smoke gate:

```bash
cd backend
python scripts/smoke_endpoints.py
```

- Analyze latency benchmark gate:

```bash
cd backend
python scripts/benchmark_analyze.py --mode e2e --samples 40 --warmup 10 --enforce-under-ms 250
```

- Optional load validation against a running backend:

```bash
cd backend
python scripts/load_validate.py --enforce --max-p95-ms 1000 --min-success-rate 99
```

## Common Make Targets

From repository root:

- `make setup`
- `make dev`
- `make test`
- `make lint`
- `make format`
- `make benchmark-analyze`
- `make load-validate`
- `make ml-gates`
- `make ml-version`

## Branch and Commit Workflow

1. Create feature/fix branch from `main`.
2. Implement code + tests together.
3. Run backend and frontend tests locally.
4. Ensure benchmark and lint checks pass.
5. Open PR with concise risk and test summary.

## Debugging Notes

- For backend dependency compatibility, prefer Python 3.11 environments.
- Keep authentication env vars aligned in local `.env` and CI configuration.
- If API behavior differs between local and container mode, validate `.env` precedence first.
