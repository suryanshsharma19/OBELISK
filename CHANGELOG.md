# Changelog

All notable changes to OBELISK will be documented in this file.

## [Unreleased]

### Documentation

- Added operations runbooks for deploy, rollback, incidents, model rollback, and migration strategy.
- Added supportability criteria, SLOs, on-call ownership, escalation path, and release sign-off ownership.
- Added release notes and refreshed release checklists.

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
