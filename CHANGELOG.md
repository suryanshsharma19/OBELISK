# Changelog

All notable changes to OBELISK will be documented in this file.

## [1.1.0] - 2026-04-22

### Added

- 5-layer ML detection pipeline fully operational with parallel async execution.
- HuggingFace model registry integration (`suryanshsharma19/obelisk-models`).
- `backend/scripts/download_models.py` — automated model download from HuggingFace (~3.7 GB).
- `backend/scripts/upload_models.py` — push updated models to HuggingFace.
- `make sync-models` target for model publishing.
- `make setup` now auto-downloads ML models from HuggingFace.
- Source code file upload in AnalyzeForm — drag-and-drop or click to upload `.js`, `.py`, `.ts`, etc.
- Official OBELISK SVG logo integrated into header with neon glow effect.
- `huggingface_hub` dependency added to `backend/requirements.txt`.

### Changed

- Complete frontend UI migration to Aegis Zero design system (void-black, neon `#00FF88`, JetBrains Mono, 0px border-radius).
- D3 dependency graph rebuilt with zoom/pan, collision physics, and brutalist square nodes.
- Dashboard statistics now driven by actual ML training metrics (84.7% accuracy, 27K+ datapoints).
- EvidenceCard component fixed to use `JSON.stringify` for nested objects (prevents `[object Object]` rendering).
- Footer stripped of obsolete internal links; only developer credits and GitHub links remain.
- Homepage stats replaced with real data from ML pipeline (training_summary.json, summary.json).

### Documentation

- Complete README rewrite with 5-layer pipeline, HuggingFace setup, and quick start guide.
- Architecture document updated with ML model provisioning, frontend design system, and analysis flow.
- Development guide updated with model management workflow and expanded Make targets.
- ML Release Checklist updated with HuggingFace sync step.
- Release Notes added for v1.1.0.
- PROJECT_INFO.txt updated to reflect current project state.

## [1.0.0] - 2026-04-16

### Added

- End-to-end package analysis pipeline across typosquatting, code, behavior, maintainer, and dependency signals.
- Authenticated package analysis/listing APIs, alerts APIs, stats APIs, crawler control APIs, and WebSocket event feed.
- Compose and Kubernetes deployment automation in GitHub Actions with post-rollout smoke checks.
- Startup/runtime readiness controls and endpoints: `/health`, `/health/ready`, `/health/worker`.
- Prometheus metrics endpoint (`/metrics`) with request, detector, cache, worker, and queue telemetry.
- Grafana application and system dashboards plus Prometheus alert rules for latency, error budget, cache efficiency, and worker backlog.
- Backend hard gates for security baseline verification, startup readiness, smoke checks, benchmark latency, and coverage thresholds.
- Expanded backend reliability tests (analyze e2e, worker retry/failure/idempotency) and frontend high-priority UI/session test coverage.

### Changed

- Security baseline enforcement for non-local environments (strong secrets, secure cookies, safe CORS).
- Request-context logging enriched with request IDs and request completion telemetry.
- Crawler batching now deduplicates package/version pairs and reports duplicate/queue metrics.
- Sandbox behavior scoped to v1.1 and excluded from current critical scoring flow.

### Operations

- Added deploy setup helper script for GitHub secrets/variables bootstrap and optional workflow dispatch.
- Added release-oriented deployment documentation with compose and Kubernetes rollout paths.

## [Unreleased]

### Documentation

- Added operations runbooks for deploy, rollback, incidents, model rollback, and migration strategy.
- Added supportability criteria, SLOs, on-call ownership, escalation path, and release sign-off ownership.
- Added release notes and refreshed release checklists.
