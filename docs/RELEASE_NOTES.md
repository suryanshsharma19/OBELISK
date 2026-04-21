# RELEASE NOTES

This document captures operator-focused release notes for shipped versions.

## 1.1.0 (2026-04-22)

### Highlights

- **5-Layer ML Detection Pipeline** is fully operational with CodeBERT, GNN, and Isolation Forest models running in parallel.
- **HuggingFace Model Registry** integrated — `make setup` now auto-downloads ~3.7 GB of pre-trained ML models from [`suryanshsharma19/obelisk-models`](https://huggingface.co/suryanshsharma19/obelisk-models). No manual model provisioning required.
- **Source Code Upload** — users can drag-and-drop or upload local source files (`.js`, `.py`, `.ts`, etc.) directly into the scanner UI for deep malware analysis.
- **Aegis Zero Frontend** — complete UI overhaul with brutalist dark theme, neon-green accents, JetBrains Mono typography, and micro-animations.
- **Interactive Dependency Graph** — rebuilt D3 visualization with zoom/pan, collision physics, and brutalist square nodes.

### ML Operations

- Added `backend/scripts/download_models.py` for automated model fetching from HuggingFace.
- Added `backend/scripts/upload_models.py` for pushing updated models to HuggingFace.
- Added `make sync-models` Makefile target.
- `make setup` now includes automatic model provisioning step.
- Dashboard statistics are now data-driven from actual ML training metrics (84.7% accuracy, 27K+ datapoints, 1.5K+ malicious samples).

### Frontend

- Migrated to Aegis Zero design system (void-black background, `#00FF88` neon accents, 0px border-radius).
- Added official OBELISK SVG logo to header with neon glow effect.
- Added file upload button to AnalyzeForm for drag-and-drop source code testing.
- Rebuilt D3 dependency graph with zoom/pan interactivity and improved physics for large dependency trees.
- Fixed EvidenceCard overflow issues with `JSON.stringify` for nested objects.

### Known Scope Boundaries

- Sandbox execution remains scoped to v1.2 and excluded from current critical scoring path.

---

## 1.0.0 (2026-04-16)

### Highlights

- Production-grade package analysis APIs and dashboard workflows are live.
- Deployment workflow now builds immutable images and rolls out to Compose or Kubernetes.
- Post-deploy smoke checks enforce auth and analyze-path validation.
- Runtime observability includes `/health/ready`, `/health/worker`, and `/metrics`.
- Prometheus alerts and Grafana dashboards are provisioned for core reliability signals.

### Reliability and Security

- Security baseline checks are enforced for non-local environments.
- Startup readiness checks validate dependency and model availability before declaring ready.
- Worker reliability and retry/idempotency behaviors are covered by backend tests.
- Frontend high-priority workflows have expanded automated coverage.

### ML Operations

- Versioned model release manifests are tracked under `backend/ml_models/saved_models/releases/`.
- `latest.json` controls active model release pointer and supports fast rollback/version pinning.

### Operations Notes

- Deploy runbook: `docs/OPERATIONS_RUNBOOK.md`
- Supportability/SLO ownership: `docs/SUPPORTABILITY.md`
- Release sign-off checklist: `docs/RELEASE_CHECKLIST.md`
- Changelog details: `CHANGELOG.md`

### Known Scope Boundaries

- Sandbox execution is intentionally scoped to v1.1 and is not in the current critical scoring path.
