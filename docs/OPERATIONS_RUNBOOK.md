# OPERATIONS RUNBOOK

This runbook defines production operating procedures for OBELISK deployments, rollback, incident response, model version rollback/pinning, and schema migrations.

## Scope

Use this runbook for non-local environments only.

- Deploy automation: `.github/workflows/deploy.yml`
- Compose rollout files: `docker-compose.yml` + `docker-compose.deploy.yml`
- Kubernetes manifests: `infrastructure/kubernetes/`
- Health and metrics endpoints: `/health`, `/health/ready`, `/health/worker`, `/metrics`

## Ownership

- Primary owner: Platform On-Call
- Secondary owner: Backend On-Call
- ML escalation owner: ML On-Call
- Security escalation owner: Security On-Call / Incident Commander

See `docs/SUPPORTABILITY.md` for escalation windows and service-level ownership.

## 1. Deploy Runbook

### 1.1 Preconditions

- Release checklist is complete in `docs/RELEASE_CHECKLIST.md`.
- Latest `main` is green in CI.
- Required deploy secrets/variables are configured (see `docs/DEPLOYMENT.md`).
- Immutable image tag to deploy is selected (default: commit SHA).

### 1.2 Execute (Preferred: GitHub Actions)

- Auto path: merge to `main`.
- Manual path: dispatch `.github/workflows/deploy.yml` with:
  - `deploy_target`: `compose` or `k8s`
  - `image_tag`: optional immutable override

Optional CLI dispatch:

```bash
gh workflow run deploy.yml -f deploy_target=compose -f image_tag=<immutable-tag>
```

### 1.3 Compose Manual Fallback

Run on deployment host in repository directory:

```bash
export BACKEND_IMAGE=ghcr.io/<owner>/obelisk-backend:<immutable-tag>
export FRONTEND_IMAGE=ghcr.io/<owner>/obelisk-frontend:<immutable-tag>

docker compose -f docker-compose.yml -f docker-compose.deploy.yml pull backend frontend
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --no-build postgres neo4j redis backend frontend
docker compose -f docker-compose.yml -f docker-compose.deploy.yml ps
```

### 1.4 Post-Deploy Validation

- `GET /health` returns `200`.
- `GET /health/ready` returns `200`.
- `GET /health/worker` returns `200`.
- `GET /metrics` returns Prometheus text format.
- Auth/login and analyze smoke flows pass.

## 2. Rollback Runbook

### 2.1 Trigger Conditions

Start rollback when one or more of the following is true:

- Smoke checks fail post-deploy.
- Error budget burn alerts fire and persist.
- Critical regression in analysis output or API behavior.
- Worker health degrades and cannot be recovered within SLO windows.

### 2.2 Application Rollback (Compose)

1. Identify last known-good backend/frontend image tags.
2. Re-point `BACKEND_IMAGE` and `FRONTEND_IMAGE` to those tags.
3. Re-run compose rollout:

```bash
export BACKEND_IMAGE=ghcr.io/<owner>/obelisk-backend:<previous-good-tag>
export FRONTEND_IMAGE=ghcr.io/<owner>/obelisk-frontend:<previous-good-tag>

docker compose -f docker-compose.yml -f docker-compose.deploy.yml pull backend frontend
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --no-build backend frontend worker
```

4. Re-run post-deploy validation checks.

### 2.3 Application Rollback (Kubernetes)

Use one of the following:

```bash
kubectl -n <namespace> rollout undo deployment/<backend-deployment>
kubectl -n <namespace> rollout undo deployment/<frontend-deployment>
```

or explicitly set prior image tags:

```bash
kubectl -n <namespace> set image deployment/<backend-deployment> <backend-container>=ghcr.io/<owner>/obelisk-backend:<previous-good-tag>
kubectl -n <namespace> set image deployment/<frontend-deployment> <frontend-container>=ghcr.io/<owner>/obelisk-frontend:<previous-good-tag>
```

### 2.4 Data and Model Rollback Coordination

- If schema changed: follow migration rollback section before/with app rollback.
- If detector behavior regressed: perform model rollback/version pinning and then restart backend + worker.

## 3. Incident Response Runbook

### 3.1 Severity Levels

- `SEV1`: User-facing outage, data integrity risk, or active security event.
- `SEV2`: Major degradation with workaround.
- `SEV3`: Minor degradation or non-critical defect.

### 3.2 Response Procedure

1. Declare incident and set severity.
2. Assign incident commander (IC) and communications owner.
3. Capture evidence:
   - `/health`, `/health/ready`, `/health/worker`, `/metrics`
   - service logs and deploy SHA/tag
   - active alerts from Prometheus/Grafana
4. Mitigate:
   - rollback release, disable noisy path, or scale/restart affected components.
5. Recover and validate:
   - run smoke checks and confirm alerts clear.
6. Close incident:
   - publish timeline, root cause, and corrective actions.

### 3.3 Security Incident Addendum

- Rotate `SECRET_KEY` and compromised credentials.
- Invalidate sessions and force re-authentication.
- Preserve forensic artifacts before cleanup.
- Follow escalation chain in `docs/SUPPORTABILITY.md`.

## 4. Model Rollback and Version Pinning

Model release pointer is stored at:

- `backend/ml_models/saved_models/releases/latest.json`

Version manifests are stored at:

- `backend/ml_models/saved_models/releases/<release_id>/manifest.json`

### 4.1 Pin to a Known-Good Model Release

```bash
python - <<'PY'
import json
from pathlib import Path

root = Path("backend/ml_models/saved_models/releases")
release_id = "<release_id>"
manifest = root / release_id / "manifest.json"
if not manifest.exists():
    raise SystemExit(f"manifest not found: {manifest}")

data = json.loads(manifest.read_text())
tmp = root / "latest.json.tmp"
tmp.write_text(json.dumps(data, indent=2) + "\n")
tmp.replace(root / "latest.json")
print(f"Pinned latest.json to release_id={release_id}")
PY
```

### 4.2 Reload Runtime

- Compose:

```bash
docker compose -f docker-compose.yml -f docker-compose.deploy.yml up -d --no-build backend worker
```

- Kubernetes:

```bash
kubectl -n <namespace> rollout restart deployment/<backend-deployment>
```

### 4.3 Validate

- `GET /health/ready` returns `200`.
- Analyze smoke request succeeds.
- Detector failure and latency alerts remain within expected ranges.

## 5. Migration Strategy Runbook

### 5.1 Strategy

Use expand-migrate-contract migration design:

- Additive schema changes first.
- Application compatibility across at least one version boundary.
- Destructive drops delayed to a later release.

### 5.2 Pre-Migration Steps

```bash
cd backend
python scripts/backup_db.py
python -m alembic current
python -m alembic history --verbose
```

### 5.3 Apply Migration

```bash
cd backend
python -m alembic upgrade head
```

### 5.4 Post-Migration Validation

- Run readiness and smoke checks.
- Validate critical API paths (`/api/auth/login`, `/api/packages/list`, `/api/packages/analyze`).
- Confirm no sustained error-budget or latency alerting.

### 5.5 Rollback Strategy

Preferred (if backward migration exists):

```bash
cd backend
python -m alembic downgrade -1
```

Fallback (irreversible migration or downgrade failure):

- Restore from latest backup artifact created by `python scripts/backup_db.py`.
- Redeploy last known-good app version.
- Re-run smoke and readiness validation.

## 6. Audit Artifacts to Capture Per Release/Incident

- Deployed image tags and commit SHA.
- Migration revision before/after deploy.
- Model `release_id` and `latest.json` content hash.
- Alert snapshots and dashboard screenshots.
- Incident timeline and post-incident action items.
