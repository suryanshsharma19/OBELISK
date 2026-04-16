# SUPPORTABILITY

This document formalizes OBELISK supportability requirements, SLOs, on-call ownership, escalation path, and release sign-off accountability.

## 1. Supportability Criteria (Production Readiness)

A release is supportable only when all criteria below are true:

1. Health and readiness endpoints are operational: `/health`, `/health/ready`, `/health/worker`.
2. Metrics endpoint `/metrics` is scraped by Prometheus.
3. Alerting rules in `monitoring/alerts/rules.yml` are active.
4. Dashboards are available in Grafana (`application.json`, `system.json`).
5. CI hard gates pass (tests, coverage, readiness, smoke, security baseline, latency benchmark).
6. Rollback path is tested and documented for app, model, and schema.
7. Release checklist in `docs/RELEASE_CHECKLIST.md` has required sign-offs.
8. Incident response and escalation ownership are assigned for the release window.

## 2. Service Level Objectives (SLOs)

| SLO | SLI / Source | Target | Alert Alignment |
|---|---|---|---|
| API availability | Successful probe ratio for `/health` and backend scrape uptime | >= 99.5% monthly | `BackendDown` |
| API error budget | 5xx ratio from `http_requests_total` | <= 1% over rolling 1h | `BackendErrorBudgetBurnSlow`, `BackendErrorBudgetBurnFast` |
| API latency | p95 request latency from `http_request_duration_seconds_bucket` | <= 1.0s over rolling 5m | `BackendHighLatencyP95` |
| Worker health | Celery worker healthy signal from `worker_health_status` | >= 99% healthy intervals (10m windows) | `WorkerUnavailable` |
| Queue saturation | Queue depth from `celery_queue_backlog` | <= 100 for 95% of 10m windows | `WorkerQueueBacklogHigh` |

SLO review cadence: weekly operational review, monthly error-budget review.

## 3. On-Call Ownership

| Responsibility | Role Owner | Backup |
|---|---|---|
| Platform runtime (infra, deploy, worker) | Platform On-Call (Primary) | Backend On-Call |
| Backend API and data path | Backend On-Call (Primary) | Platform On-Call |
| Model quality and artifact regressions | ML On-Call | Backend On-Call |
| Security incidents | Security On-Call / Incident Commander | Platform Lead |
| Release go/no-go decision | Release Manager | Engineering Manager |

Use team aliases and pager schedules that map to these roles in your incident tooling.

## 4. Escalation Path

1. `T+0 to T+15 min`: Primary on-call acknowledges, triages, and starts incident log.
2. `T+15 to T+30 min`: Escalate to secondary owner if unresolved or blast radius grows.
3. `T+30 to T+60 min`: Engage Incident Commander and release owner; decide rollback vs hotfix.
4. `T+60+ min`: Executive/security escalation for SEV1 or customer-impacting security events.

Escalation triggers:

- `BackendDown` critical alert sustained for >= 2 minutes.
- Error budget burn-fast alert sustained for >= 5 minutes.
- Any active data integrity or security compromise signal.

## 5. Release Checklist Sign-off Owner

- Sign-off owner: Release Manager (single accountable owner per release).
- Required co-signers: Platform On-Call, Security On-Call (or delegate), and ML On-Call when model artifacts changed.
- Sign-off record location: release PR description and `docs/RELEASE_NOTES.md` entry.

Checklist template and required approvals are defined in `docs/RELEASE_CHECKLIST.md`.

## 6. Related Operational Docs

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/DEPLOYMENT.md`
- `docs/ML_RELEASE_CHECKLIST.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/RELEASE_NOTES.md`
