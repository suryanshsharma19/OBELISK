# RELEASE NOTES

This document captures operator-focused release notes for shipped versions.

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
