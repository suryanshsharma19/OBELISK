<p align="center">
  <img src="docs/diagrams/obelisk.svg" alt="OBELISK logo" width="140" />
</p>

<h1 align="center">OBELISK</h1>

<p align="center"><b>Omniscient Behavioral Entity Leveraging Intelligent Surveillance for Kill-chain Prevention.</b></p>

<p align="center">
  AI-powered software supply chain security platform that detects malicious npm and PyPI packages through a 5-layer ML analysis pipeline, interactive dependency graph intelligence, and real-time threat reporting.
</p>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=white)](https://react.dev/)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97-Models-yellow)](https://huggingface.co/suryanshsharma19/obelisk-models)

---

## Table of Contents

- [What OBELISK Does](#what-obelisk-does)
- [5-Layer Detection Pipeline](#5-layer-detection-pipeline)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Repository Layout](#repository-layout)
- [Quick Start](#quick-start)
- [ML Model Management](#ml-model-management)
- [Local Development](#local-development)
- [API Surface](#api-surface)
- [Testing](#testing)
- [CI/CD PR and Commit Security Gate](#cicd-pr-and-commit-security-gate)
- [ML Operations](#ml-operations)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)

---

## What OBELISK Does

Software supply chain attacks are increasingly sophisticated and often impossible to detect with static indicators alone. OBELISK combines five distinct machine learning and heuristic analysis layers to produce an aggregated risk score for any npm or PyPI package:

1. **Typosquatting Detection** — Levenshtein distance and phonetic similarity scoring against a corpus of popular packages to catch name-squatting attacks.
2. **Code Analysis** — CodeBERT transformer-based static analysis of source code combined with AST pattern matching and regex heuristics to identify obfuscated payloads, `eval()` injection, and data exfiltration patterns.
3. **Behavioral Analysis** — Runtime behavioral profiling including sandbox network call detection, process spawning, filesystem access patterns, and install-script analysis.
4. **Maintainer Risk Scoring** — Isolation Forest anomaly detection on maintainer metadata (account age, package count, download history, verified email status) to flag brand-new or suspicious publisher accounts.
5. **Dependency Graph Analysis** — Graph Neural Network (GNN) powered traversal of the full dependency tree via Neo4j to propagate risk from transitive dependencies and detect malicious dependency chains.

Each detector runs in parallel and feeds into a weighted risk scorer with calibration logic, producing explainable threat assessments with full evidence breakdowns.

---

## 5-Layer Detection Pipeline

| Layer | Detector Module | ML Model | Weight |
|---|---|---|---|
| Typosquatting | `typosquat.py` | Levenshtein + phonetic heuristics | 25% |
| Code Analysis | `code_analyzer.py` | CodeBERT (fine-tuned `.safetensors`) + AST + regex | 35% |
| Behavioral | `behavior_analyzer.py` | Sandbox profiling + metadata heuristics | 15% |
| Maintainer Risk | `anomaly_detector.py` | Isolation Forest (`model.joblib`) | 15% |
| Dependency Graph | `gnn_analyzer.py` | GNN (`model.pt`) + Neo4j traversal | 10% |

**Aggregate Risk Score** = Σ (detector_score × weight), capped at 100, with calibration dampening if only a single detector fires.

**Threat Levels**: Safe (0–20) → Low (20–40) → Medium (40–60) → High (60–80) → Critical (80–100)

---

## Key Features

- **5-Layer ML Analysis Pipeline** — parallel execution of typosquatting, code analysis, behavioral, maintainer, and dependency detectors
- **Source Code Upload** — drag-and-drop or upload local source files (`.js`, `.py`, `.ts`, etc.) directly into the scanner UI for deep analysis
- **Interactive Dependency Graph** — D3-powered force-directed graph visualization with zoom, pan, and collision physics
- **Real-Time Threat Feed** — WebSocket-powered live event stream for analysis completions and threat alerts
- **Automated Model Provisioning** — pre-trained ML models (3.7 GB) hosted on HuggingFace and auto-downloaded during `make setup`
- **Aegis Zero UI** — brutalist, high-contrast dark interface with neon-green accents, JetBrains Mono typography, and micro-animations
- **CI/CD Integration** — reusable GitHub Action for dependency scanning in external repositories
- **Full Observability** — Prometheus metrics, Grafana dashboards, and structured logging

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        React Frontend                           │
│  (Aegis Zero UI · Redux · D3 Dependency Graph · Source Upload)  │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API + WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                       FastAPI Backend                           │
│                                                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Typosquat │ │CodeBERT  │ │Behavioral│ │Isolation │ │  GNN   │ │
│  │Detector  │ │Analyzer  │ │Analyzer  │ │Forest    │ │Analyzer│ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬────┘ │
│       └────────────┴────────────┴────────────┴───────────┘      │
│                          Risk Scorer                            │
└──────┬───────────────────┬───────────────────┬──────────────────┘
       │                   │                   │
  ┌────▼─────┐        ┌─────▼─────┐       ┌────▼────┐
  │PostgreSQL│        │   Neo4j   │       │  Redis  │
  │(Packages,│        │(Dependency│       │ (Cache) │
  │Analyses, │        │  Graphs)  │       │         │
  │ Alerts)  │        │           │       │         │
  └──────────┘        └───────────┘       └─────────┘
```

Available architecture diagrams:

- [System Architecture](docs/diagrams/system-architecture.png)
- [ML Detection Pipeline](docs/diagrams/ml-detection-pipeline.png)
- [Database Schema](docs/diagrams/database-schema.png)
- [Deployment Architecture](docs/diagrams/deployment-architecture.png)

---

## Technology Stack

### Backend
- Python 3.11+ · FastAPI · SQLAlchemy + Alembic · Celery
- PyTorch · HuggingFace Transformers · scikit-learn · torch-geometric
- `huggingface_hub` for automated model sync

### Frontend
- React 18 · Redux Toolkit · React Router · Recharts · D3.js
- Aegis Zero design system (Tailwind CSS · JetBrains Mono · brutalist aesthetic)

### Data Stores & Infrastructure
- PostgreSQL 15 · Neo4j 5 · Redis 7
- Docker Compose · Kubernetes manifests · Terraform modules

### ML Model Registry
- HuggingFace Hub: [`suryanshsharma19/obelisk-models`](https://huggingface.co/suryanshsharma19/obelisk-models)
- ~3.7 GB of pre-trained weights (CodeBERT `.safetensors`, GNN `.pt`, Isolation Forest `.joblib`)

---

## Repository Layout

```text
OBELISK/
  backend/                FastAPI app, ML detectors, analysis service, scripts
    app/
      ml/                 5 detector modules + risk scorer
      services/           Analysis orchestration, registry monitor, sandbox
      api/routes/         REST + WebSocket endpoints
    ml_models/            Training pipelines, datasets, saved model weights
    scripts/              download_models.py, upload_models.py, init_db, seed_data
  frontend/               React application (Aegis Zero UI)
    src/
      components/         PackageAnalysis, Dashboard, common UI components
      pages/              HomePage, AnalyzePage, DashboardPage, AlertsPage
  docs/                   Architecture, API, deployment, security documentation
  infrastructure/         Docker, Kubernetes, Terraform assets
  monitoring/             Prometheus and Grafana configuration
  scripts/                Project-level automation (adversarial suite, CI scanner)
```

---

## Quick Start

### Prerequisites

- **Docker & Docker Compose** (required for database services)
- **Python 3.11+**
- **Node.js 18+** and **npm**
- **Make** (pre-installed on Linux/Mac; Windows users should use WSL)

### 1. Clone the repository

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

### 3. Run setup (installs dependencies + downloads ML models)

```bash
make setup
```

> **What happens:** This creates a Python virtual environment, installs all backend/frontend dependencies, and **automatically downloads ~3.7 GB of pre-trained ML models** from [HuggingFace](https://huggingface.co/suryanshsharma19/obelisk-models) into `backend/ml_models/saved_models/`. No manual model setup required.

### 4. Start the full stack

```bash
make dev
```

### 5. Access services

| Service | URL |
|---|---|
| Frontend (Aegis Zero UI) | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| Neo4j Browser | http://localhost:7474 |

### 6. Analyze a package

1. Open http://localhost:3000 and click **SCAN YOUR DEPENDENCIES**
2. Enter a package name (e.g., `express`, `lodash`, `requests`) and version
3. Optionally **upload a source file** using the **UPLOAD FILE** button to test raw code against all 5 detectors
4. View the analysis results including risk breakdown, evidence cards, and interactive dependency graph

### 7. Shut down

```bash
make down
```

---

## ML Model Management

### Automatic Download (for users cloning the repo)

Running `make setup` automatically fetches all pre-trained models from HuggingFace. If models already exist locally, the download is skipped. Force re-download with:

```bash
cd backend && python scripts/download_models.py --force
```

### Upload Updated Models (for maintainers)

After training new models, push them to HuggingFace:

```bash
make sync-models
```

This uploads the entire `backend/ml_models/saved_models/` directory to [`suryanshsharma19/obelisk-models`](https://huggingface.co/suryanshsharma19/obelisk-models).

### Train Models Locally

To train miniature models from scratch on your own machine:

```bash
make datasets-quick    # Fetch 50 malicious + 50 benign samples
make ml-pipeline       # Train CodeBERT, GNN, and Isolation Forest models
```

---

## Local Development

### Recommended: Make targets

```bash
make setup          # Install deps + download ML models from HuggingFace
make dev            # Start all services (Docker Compose)
make down           # Stop all services
make clean          # Stop and remove volumes/cache
make test           # Run backend test suite
make lint           # Run linters
make format         # Format code
make sync-models    # Push ML models to HuggingFace
make ml-pipeline    # Run full train/eval/gate/version pipeline
make adversarial-check  # Run adversarial malware test suite
```

### Manual backend/frontend startup

Backend:

```bash
cd backend
python -m venv .venv311
source .venv311/bin/activate
pip install -r requirements.txt
python scripts/download_models.py
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

---

## API Surface

Core routes exposed by the backend:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Service status |
| `GET` | `/health` | Health check |
| `GET` | `/health/ready` | Readiness probe |
| `GET` | `/health/worker` | Worker health |
| `GET` | `/metrics` | Prometheus metrics |
| `POST` | `/api/auth/login` | JWT authentication |
| `POST` | `/api/packages/analyze` | Submit package for 5-layer analysis |
| `GET` | `/api/packages/list` | List analyzed packages |
| `GET` | `/api/packages/{id}` | Package detail with breakdown |
| `GET` | `/api/stats/overview` | Dashboard statistics |
| `GET` | `/api/alerts/` | Alert listing |
| `POST` | `/api/crawler/start` | Start registry crawler |
| `WS` | `/ws` | Real-time event stream |

See [docs/API.md](docs/API.md) for full request/response documentation.

---

## Testing

```bash
make test                    # Backend pytest suite
make adversarial-check       # Synthetic malware adversarial suite
make load-validate           # Backend concurrency/load testing
make benchmark-analyze       # Analyze endpoint latency benchmarks
```

---

## CI/CD PR and Commit Security Gate

OBELISK includes automated CI gates for pull requests and commits to catch security, quality, and runtime regressions before merge.

### Included workflows

- `Backend Tests` (`.github/workflows/backend-tests.yml`) on `push` and `pull_request`
- `Frontend Tests` (`.github/workflows/frontend-tests.yml`) on `push` and `pull_request`
- `OBELISK Scan Example` (`.github/workflows/obelisk-scan-example.yml`) on `pull_request`, `push` to `main`, and manual dispatch

### What the OBELISK scan gate enforces

- Blocks CI when `threat_level` is `high` or `critical` (configurable)
- Blocks CI when `risk_score >= 60` (configurable)
- Fails on unresolved dependency versions in strict mode
- Fails on scanner/API errors in strict mode

### How to use this feature in your repository

1. Configure repository secrets:
  - `OBELISK_API_BASE_URL`
  - `OBELISK_AUTH_USERNAME`
  - `OBELISK_AUTH_PASSWORD`
2. Open a PR or push a commit.
3. Verify workflow results in GitHub Actions.
4. Enable branch protection and mark CI checks as required to block merge when checks fail.

See the full usage guide in [docs/CI_INTEGRATION.md](docs/CI_INTEGRATION.md), including external repository setup and reusable action details.

---

## ML Operations

The ML pipeline includes model training, evaluation, acceptance gates, and versioned artifact management.

```bash
make datasets-quick       # Build small training dataset
make datasets             # Build full training dataset
make ml-pipeline          # Train → evaluate → gate → version
make ml-gates             # Enforce acceptance thresholds
make ml-version           # Generate versioned release manifest
make sync-models          # Push models to HuggingFace
```

For detailed ML release procedures, see [docs/ML_RELEASE_CHECKLIST.md](docs/ML_RELEASE_CHECKLIST.md).

---

## Deployment

OBELISK supports multiple deployment targets:

- **Docker Compose** — single-host development and staging
- **Kubernetes** — production orchestration via manifests in `infrastructure/kubernetes/`
- **Terraform** — infrastructure provisioning via modules in `infrastructure/terraform/`

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for full deployment guide.

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/ARCHITECTURE.md) | System design, data flow, ML pipeline |
| [Development Guide](docs/DEVELOPMENT.md) | Local setup, quality gates, debugging |
| [API Reference](docs/API.md) | Endpoint documentation |
| [Deployment Guide](docs/DEPLOYMENT.md) | Docker, Kubernetes, Terraform deployment |
| [CI Integration](docs/CI_INTEGRATION.md) | Reusable GitHub Action for external repos |
| [Security Guide](docs/SECURITY.md) | Auth model, hardening checklist |
| [ML Release Checklist](docs/ML_RELEASE_CHECKLIST.md) | Model training and release procedures |
| [Operations Runbook](docs/OPERATIONS_RUNBOOK.md) | Deploy, rollback, incident response |
| [Supportability](docs/SUPPORTABILITY.md) | SLOs, on-call ownership, escalation |
| [Release Checklist](docs/RELEASE_CHECKLIST.md) | Production release sign-off |
| [Release Notes](docs/RELEASE_NOTES.md) | Version release summaries |
| [Contributing](docs/CONTRIBUTING.md) | Contribution workflow and standards |

---

## Contributing

Contributions are welcome. Please read [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) before opening a pull request.

---

## License

Licensed under the MIT License. See [LICENSE](LICENSE).
