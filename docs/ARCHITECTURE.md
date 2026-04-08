# ARCHITECTURE

## System Overview

OBELISK is a full-stack supply-chain threat analysis platform built around a FastAPI backend and React frontend.

Primary runtime layers:

1. Frontend (React + Redux): dashboard, package analysis workflow, alerts, crawler status.
2. Backend API (FastAPI): authentication, analysis orchestration, stats, alert and crawler control.
3. Data tier:
	- PostgreSQL for package, analysis, and alert entities.
	- Neo4j for dependency graph relationships.
	- Redis for cache and async coordination.
4. ML tier: detector modules for typosquatting, code patterns/model inference, behavior analysis, anomaly analysis, and dependency graph risk.

## Backend Layering

- `app/api/routes`: HTTP and WebSocket endpoints.
- `app/services`: orchestration and business rules.
- `app/ml`: detector implementations and score aggregation.
- `app/db`: SQLAlchemy models/session and external datastore clients.
- `app/core`: auth, security controls, logging, exception handling.

This separation keeps endpoint code thin and pushes decision logic into services and ML modules.

## Analysis Request Flow

For `POST /api/packages/analyze`:

1. Request validated by Pydantic schema.
2. Auth and rate-limiting dependencies are enforced.
3. Analysis service performs metadata retrieval and detector execution.
4. Scores are aggregated by risk scorer.
5. Results are persisted and returned in a single response contract.

## Security Model

- JWT bearer authentication for protected routes.
- Centralized credential validation and token creation.
- Security headers added globally via middleware.
- Rate-limit dependency on sensitive endpoints.
- HttpOnly cookie support for browser auth compatibility.

## Real-Time Path

WebSocket endpoint `/ws` supports authenticated sessions and basic heartbeat (`ping/pong`) for connection liveness.

## Operational Topology

- Local development primarily uses Docker Compose.
- Production deployment paths include Kubernetes manifests and Terraform infrastructure modules.
- Monitoring stack includes Prometheus and Grafana for metrics and dashboards.

## Design Goals

1. Fast threat analysis response times for package scans.
2. Explainable evidence for risk decisions.
3. Practical separation of concerns for maintainability.
4. CI-enforced quality gates (tests, coverage, benchmark checks).
