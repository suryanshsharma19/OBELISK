# DEVELOPMENT

## Local Prerequisites

- Python 3.11 (recommended for backend parity with CI).
- Node.js 18+ for frontend.
- Docker and Docker Compose for full-stack runtime (PostgreSQL, Neo4j, Redis).
- Make (pre-installed on Linux/Mac; use WSL on Windows).

## Quick Setup (Recommended)

```bash
make setup    # Creates venv, installs deps, downloads ~3.7 GB ML models from HuggingFace
make dev      # Starts all services via Docker Compose
```

## Backend Setup (Manual)

```bash
cd backend
python -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
python scripts/download_models.py     # Fetch ML models from HuggingFace
python scripts/init_db.py
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Frontend Setup

```bash
cd frontend
npm install
npm start
```

The frontend runs on http://localhost:3000 with the Aegis Zero design system (brutalist dark theme, neon-green accents).

## ML Model Management

### Download models (runs automatically during `make setup`)

```bash
cd backend && python scripts/download_models.py
```

Models are fetched from [`suryanshsharma19/obelisk-models`](https://huggingface.co/suryanshsharma19/obelisk-models) on HuggingFace (~3.7 GB). If models already exist locally, the download is skipped. Use `--force` to overwrite.

### Upload updated models (maintainers only)

```bash
make sync-models
```

This pushes the entire `backend/ml_models/saved_models/` directory to HuggingFace.

### Train models locally

```bash
make datasets-quick    # Fetch small training dataset (50 malicious + 50 benign)
make datasets          # Fetch full training dataset
make ml-pipeline       # Train CodeBERT, GNN, Isolation Forest → evaluate → gate → version
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

- Adversarial malware test suite:

```bash
make adversarial-check
```

- Optional load validation:

```bash
cd backend
python scripts/load_validate.py --enforce --max-p95-ms 1000 --min-success-rate 99
```

## Common Make Targets

From repository root:

| Command | Description |
|---|---|
| `make setup` | Install deps + download ML models from HuggingFace |
| `make dev` | Start full stack (Docker Compose) |
| `make down` | Stop all services |
| `make clean` | Stop and remove volumes/cache |
| `make test` | Run backend test suite |
| `make lint` | Run linters |
| `make format` | Format code |
| `make sync-models` | Push ML models to HuggingFace |
| `make ml-pipeline` | Full ML train/eval/gate/version pipeline |
| `make adversarial-check` | Synthetic adversarial malware suite |
| `make benchmark-analyze` | Analyze endpoint latency benchmark |
| `make load-validate` | Backend concurrency/load testing |
| `make datasets-quick` | Build small training dataset |

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
- If ML models fail to load, run `python scripts/download_models.py --force` to re-fetch from HuggingFace.
