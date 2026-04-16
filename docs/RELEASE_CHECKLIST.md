# RELEASE CHECKLIST

Use this checklist for every production release.

## 1. Release Metadata

- Release version/tag: `__________`
- Release date (UTC): `__________`
- Commit SHA: `__________`
- Deployment target: `compose` / `k8s`
- Sign-off owner (Release Manager): `__________`

## 2. Build and Quality Gates

- [ ] Backend CI passed (tests + coverage threshold).
- [ ] Frontend CI passed (unit tests + build).
- [ ] Security baseline gate passed (`backend/scripts/verify_runtime_security.py --strict --require-non-local`).
- [ ] Startup readiness gate passed (`backend/scripts/check_startup_readiness.py --strict --include-dependencies`).
- [ ] Smoke endpoints gate passed (`backend/scripts/smoke_endpoints.py`).
- [ ] Analyze latency gate passed (`backend/scripts/benchmark_analyze.py --mode e2e`).

## 3. Deployment Readiness

- [ ] Required GitHub deploy secrets and variables are present.
- [ ] Rollback image tags are identified and documented.
- [ ] Operational runbook reviewed (`docs/OPERATIONS_RUNBOOK.md`).
- [ ] Dashboards and alerts verified for target environment.

## 4. Database and Migration Readiness

- [ ] Migration impact reviewed (`python -m alembic history --verbose`).
- [ ] Fresh backup completed (`python backend/scripts/backup_db.py`).
- [ ] Migration plan documented (expand-migrate-contract where applicable).
- [ ] Downgrade or restore fallback validated.

## 5. Model Release Readiness (If ML Artifacts Changed)

- [ ] `docs/ML_RELEASE_CHECKLIST.md` completed.
- [ ] `backend/ml_models/saved_models/releases/latest.json` points to intended `release_id`.
- [ ] Known-good fallback `release_id` recorded.
- [ ] Detector regression notes captured.

## 6. Post-Deploy Verification

- [ ] `GET /health` returns `200`.
- [ ] `GET /health/ready` returns `200`.
- [ ] `GET /health/worker` returns `200`.
- [ ] `GET /metrics` scrape is successful.
- [ ] Auth and analyze smoke flow validated in deployed environment.

## 7. Required Sign-offs

Sign-off owner (single accountable owner): Release Manager.

- [ ] Release Manager (required)
- [ ] Platform On-Call (required)
- [ ] Security On-Call or delegate (required)
- [ ] Backend On-Call (required)
- [ ] ML On-Call (required when model artifacts changed)

## 8. Release Record

- Release notes updated in `docs/RELEASE_NOTES.md`.
- Changelog entry updated in `CHANGELOG.md`.
- Incident watch window owner assigned for first 24h after deploy.
