<p align="center">
  <img src="docs/diagrams/obelisk.svg" alt="OBELISK logo" width="140" />
</p>

<h1 align="center">OBELISK</h1>

<p align="center">Omniscient Behavioral Entity Leveraging Intelligent Surveillance for Kill-chain Prevention.</p>

OBELISK is an AI-assisted software supply chain security platform focused on detecting potentially malicious npm and PyPI packages through a multi-signal analysis pipeline, graph intelligence, and actionable risk reporting.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)

## Table of Contents

- [What OBELISK Does](#what-obelisk-does)
- [Key Capabilities](#key-capabilities)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Layout](#repository-layout)
- [Quick Start (Docker Compose)](#quick-start-docker-compose)
- [Local Development](#local-development)
- [API Surface](#api-surface)
- [Observability and Monitoring](#observability-and-monitoring)
- [Testing](#testing)
- [ML Operations](#ml-operations)
- [Deployment](#deployment)
- [Operations and Supportability](#operations-and-supportability)
- [Security and Configuration Notes](#security-and-configuration-notes)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

## What OBELISK Does

Software supply chain attacks are increasingly sophisticated and often difficult to detect with static indicators alone. OBELISK combines:

- package metadata analysis
- code and behavior heuristics
- graph-based dependency risk signals
- weighted score aggregation

The platform is designed to help security teams evaluate package risk quickly, monitor registry activity, and triage high-risk findings through a unified API and dashboard.

## Key Capabilities

- Multi-detector analysis pipeline for npm and PyPI packages
- Weighted risk scoring and threat classification
- Real-time crawler controls and WebSocket event feed
- Dependency graph analysis with Neo4j-backed traversal
- Caching with Redis for repeat analysis efficiency
- Alerting and dashboard statistics endpoints
- Containerized local environment with PostgreSQL, Neo4j, Redis, backend, and frontend

## Architecture

At a high level:

1. React frontend provides analyst workflows for analysis, crawler operations, and alerts.
2. FastAPI backend orchestrates detectors, scoring, persistence, and API responses.
3. PostgreSQL stores core relational entities.
4. Neo4j stores and queries dependency graph relationships.
5. Redis provides low-latency cache support.

Available architecture diagrams:

- [System Architecture](docs/diagrams/system-architecture.png)
- [ML Detection Pipeline](docs/diagrams/ml-detection-pipeline.png)
- [Database Schema](docs/diagrams/database-schema.png)
- [Deployment Architecture](docs/diagrams/deployment-architecture.png)

## Technology Stack

### Backend

- Python 3.10+
- FastAPI
- SQLAlchemy + Alembic
- Celery
- PyTorch, Transformers, scikit-learn, torch-geometric

### Frontend

- React 18
- Redux Toolkit
- React Router
- Recharts and D3

### Data Stores and Infrastructure

- PostgreSQL 15
- Neo4j 5
- Redis 7
- Docker Compose
- Kubernetes manifests and Terraform modules

## Repository Layout

```text
OBELISK/
  backend/         FastAPI app, ML modules, scripts, tests
  frontend/        React application
  docs/            Architecture, API, deployment, security docs
  infrastructure/  Docker, Kubernetes, Terraform assets
  monitoring/      Prometheus and Grafana configuration
  scripts/         Project-level automation scripts
```

## Quick Start (Docker Compose)

### 1. Clone and enter the repository

```bash
git clone https://github.com/suryanshsharma19/OBELISK.git
cd OBELISK
```

### 2. Create environment files

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

### 3. Start the full stack

```bash
docker-compose up -d
```

### 4. Access services

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Neo4j Browser: http://localhost:7474

## Local Development

### Option A: Make targets (recommended for consistency)

```bash
make setup
make dev
```

Useful targets:

- `make down` stop services
- `make clean` stop and remove volumes/cache artifacts
- `make test` run backend tests
- `make datasets-quick` build a small local dataset bundle
- `make datasets` build a larger dataset bundle
- `make datasets-offline` rebuild processed files from local raw cache
- `make load-validate` run backend concurrency/load validation
- `make benchmark-analyze` benchmark package analysis endpoint
- `make ml-gates` enforce ML acceptance thresholds
- `make ml-version` generate versioned ML artifact manifest
- `make ml-pipeline` run train/eval/gate/version pipeline

### Option B: Manual backend/frontend startup

Backend:

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python scripts/init_db.py
python scripts/seed_data.py
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend (new terminal):

```bash
cd frontend
npm install
npm start
```

## API Surface

Core routes exposed by the backend include:

- `GET /` service status
- `GET /health` health check
- `POST /api/auth/login` authentication
- `GET /api/packages` list package analyses
- `POST /api/packages/analyze` submit package for analysis
- `GET /api/stats` dashboard statistics
- `GET /api/alerts` alert listing
- `POST /api/crawler/start` start crawler
- `POST /api/crawler/stop` stop crawler
- `WS /ws` real-time event stream

See [docs/API.md](docs/API.md) and [docs/api/openapi.yaml](docs/api/openapi.yaml) for details.

## Observability and Monitoring

Runtime observability endpoints exposed by the backend:

- `GET /health` liveness and startup-readiness status
- `GET /health/ready` readiness gate (returns `503` when degraded)
- `GET /health/worker` Celery worker + queue health snapshot
- `GET /metrics` Prometheus metrics endpoint

Monitoring assets live under `monitoring/`:

- Prometheus scrape + rules: `monitoring/prometheus/prometheus.yml`
- Alert rules: `monitoring/alerts/rules.yml`
- Grafana dashboards: `monitoring/grafana/dashboards/application.json` and `monitoring/grafana/dashboards/system.json`
- Grafana dashboard provisioning: `monitoring/grafana/provisioning/dashboards.yaml`

When running the infrastructure compose stack (`infrastructure/docker/docker-compose.yml`), dashboards are provisioned by mounting:

- `monitoring/grafana/provisioning` -> `/etc/grafana/provisioning`
- `monitoring/grafana/dashboards` -> `/var/lib/grafana/dashboards`

## Testing

### Full suite helper

```bash
./scripts/run_tests.sh all
```

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```

## ML Operations

The repository includes model and dataset workflows under backend/ml_models and automation targets in the top-level Makefile.

For reproducibility and release checks, see:

- [docs/ML_RELEASE_CHECKLIST.md](docs/ML_RELEASE_CHECKLIST.md)
- `make ml-pipeline`
- `make ml-version`

## Deployment

Deployment paths are available for:

- Docker Compose
- Kubernetes manifests in infrastructure/kubernetes
- Terraform modules in infrastructure/terraform

Deployment guide: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

## Operations and Supportability

Operational runbooks and ownership references:

- [Operations Runbook](docs/OPERATIONS_RUNBOOK.md)
- [Supportability (SLOs, On-Call, Escalation)](docs/SUPPORTABILITY.md)
- [Release Checklist (Sign-off Owner)](docs/RELEASE_CHECKLIST.md)
- [Release Notes](docs/RELEASE_NOTES.md)

## Security and Configuration Notes

- Default credentials and secrets in example env files are for local development only.
- Set strong values for `SECRET_KEY`, database passwords, and auth credentials before non-local use.
- Restrict CORS origins and review security headers and auth settings in backend configuration.

Security reference: [docs/SECURITY.md](docs/SECURITY.md)

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [API Reference](docs/API.md)
- [Contributing Guide](docs/CONTRIBUTING.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Security Guide](docs/SECURITY.md)
- [Operations Runbook](docs/OPERATIONS_RUNBOOK.md)
- [Supportability Guide](docs/SUPPORTABILITY.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)
- [Release Notes](docs/RELEASE_NOTES.md)

## Contributing

Contributions are welcome. Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before opening a pull request.

## License

Licensed under the MIT License. See [LICENSE](LICENSE).
