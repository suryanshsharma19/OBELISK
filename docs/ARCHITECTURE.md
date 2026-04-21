# ARCHITECTURE

## System Overview

OBELISK is a full-stack AI-powered supply chain threat analysis platform. It combines a FastAPI backend with five parallel ML detection layers, a React frontend (Aegis Zero design system), and a tri-store data tier (PostgreSQL, Neo4j, Redis).

### Runtime Layers

1. **Frontend (React + Redux)**: Aegis Zero brutalist UI providing package analysis workflow, source code upload, interactive D3 dependency graphs, alert management, and real-time WebSocket threat feed.
2. **Backend API (FastAPI)**: Authentication, 5-layer analysis orchestration, weighted risk scoring, alert management, crawler control, and Prometheus metrics.
3. **ML Tier**: Five parallel detectors:
   - **Typosquatting Detector** — Levenshtein distance and phonetic similarity against popular package corpus (weight: 25%)
   - **Code Analyzer** — Fine-tuned CodeBERT transformer (`.safetensors`) combined with AST parsing and regex heuristics (weight: 35%)
   - **Behavior Analyzer** — Sandbox profiling, install-script analysis, network call detection (weight: 15%)
   - **Anomaly Detector** — Isolation Forest model (`.joblib`) for maintainer metadata anomaly scoring (weight: 15%)
   - **GNN Analyzer** — Graph Neural Network (`.pt`) for dependency graph risk propagation via Neo4j (weight: 10%)
4. **Data Tier**:
   - PostgreSQL 15 for package, analysis, and alert entities.
   - Neo4j 5 for dependency graph relationships and traversal.
   - Redis 7 for analysis cache and async coordination.
5. **Model Registry**: Pre-trained ML models (~3.7 GB) are hosted on [HuggingFace](https://huggingface.co/suryanshsharma19/obelisk-models) and auto-downloaded during `make setup` via `huggingface_hub` Python API.

## Backend Layering

- `app/api/routes`: HTTP and WebSocket endpoints.
- `app/services`: Orchestration and business rules (analysis_service, registry_monitor, sandbox, graph_service).
- `app/ml`: Detector implementations (typosquat, code_analyzer, behavior_analyzer, anomaly_detector, gnn_analyzer) and risk scorer with calibration logic.
- `app/db`: SQLAlchemy models/session and external datastore clients (Neo4j, Redis).
- `app/core`: Auth, security controls, logging, exception handling, observability.

This separation keeps endpoint code thin and pushes decision logic into services and ML modules.

## Analysis Request Flow

For `POST /api/packages/analyze`:

1. Request validated by Pydantic schema (accepts package name, version, registry, and optional raw source code).
2. Auth and rate-limiting dependencies are enforced.
3. Cache check via Redis — if hit, returns immediately.
4. Registry metadata is fetched (npm/PyPI).
5. If source code was uploaded or pasted, it is passed directly to detectors; otherwise, code is fetched from the registry.
6. All 5 detectors execute in parallel via `asyncio.gather()`.
7. Risk scorer aggregates weighted scores with calibration dampening.
8. Results are persisted to PostgreSQL and Neo4j.
9. Cached in Redis (1-hour TTL).
10. If threat level is high/critical, an alert is automatically created.
11. WebSocket broadcast to connected clients.

## ML Model Provisioning

Pre-trained models are hosted at `suryanshsharma19/obelisk-models` on HuggingFace.

- **Download**: `backend/scripts/download_models.py` uses `huggingface_hub.snapshot_download()` to fetch the full model suite into `backend/ml_models/saved_models/`.
- **Upload**: `backend/scripts/upload_models.py` uses `HfApi.upload_folder()` to push updated models.
- **Makefile integration**: `make setup` auto-triggers download; `make sync-models` pushes updates.

Models loaded at startup:
- `codebert/` — Fine-tuned CodeBERT for malicious code detection
- `gnn/` or `gnn_best/` — GNN for dependency graph risk scoring
- `isolation_forest/` — Isolation Forest for maintainer anomaly detection

## Frontend Architecture

The React frontend uses the **Aegis Zero** design system:
- Void-black (`#0a0a0a`) background with neon-green (`#00FF88`) accent palette
- JetBrains Mono monospace font for terminal aesthetic
- Brutalist 0px border-radius, heavy 2px borders
- D3.js force-directed dependency graph with zoom/pan and collision physics
- Source code file upload via `FileReader` API for drag-and-drop malware testing

## Security Model

- JWT bearer authentication for protected routes.
- Centralized credential validation and token creation.
- Security headers added globally via middleware.
- Rate-limit dependency on sensitive endpoints.
- HttpOnly cookie support for browser auth compatibility.

## Real-Time Path

WebSocket endpoint `/ws` supports authenticated sessions, heartbeat (`ping/pong`), and broadcasts analysis completions and threat detections to connected clients.

## Operational Topology

- Local development uses Docker Compose (`make dev`).
- Production deployment paths include Kubernetes manifests and Terraform modules.
- Monitoring stack includes Prometheus and Grafana for metrics and dashboards.

## Design Goals

1. Fast threat analysis response times via parallel detector execution and Redis caching.
2. Explainable evidence for every risk decision with full detector breakdown.
3. Practical separation of concerns for maintainability.
4. CI-enforced quality gates (tests, coverage, benchmark checks, adversarial malware suite).
5. Zero-configuration model setup via automated HuggingFace provisioning.
