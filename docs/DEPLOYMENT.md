# DEPLOYMENT

## Deployment Targets

OBELISK supports:

1. Docker Compose (single-host/dev).
2. Kubernetes (production-style orchestration).
3. Terraform-backed infrastructure provisioning.

CI/CD deployment automation is implemented in `.github/workflows/deploy.yml` and supports:

1. Build and push backend/frontend images to GHCR.
2. Rollout to either Compose (SSH target) or Kubernetes.
3. Post-rollout smoke checks against production endpoints.

Operational runbooks and ownership references:

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/RELEASE_CHECKLIST.md`
- `docs/SUPPORTABILITY.md`

## Docker Compose Deployment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker-compose up -d --build
```

For CI/CD-driven Compose rollout, the deploy workflow uses:

1. `docker-compose.yml`
2. `docker-compose.deploy.yml`

The override file injects immutable image references and enforces startup readiness checks.

Post-deploy checks:

- Backend health: `GET /health`
- Auth flow: `POST /api/auth/login`
- Analyze endpoint: `POST /api/packages/analyze`
- Frontend availability: port `3000`

## Kubernetes Deployment

Key manifests are under `infrastructure/kubernetes`.

Recommended sequence:

1. Build and push immutable backend/frontend images.
2. Create namespace and config maps.
3. Create real secrets from secure pipeline input (do not use defaults from repository).
4. Apply deployments/services/ingress.
5. Validate probes, logs, and metrics.

Example:

```bash
kubectl apply -f infrastructure/kubernetes/
```

For CI/CD-driven Kubernetes rollout, the deploy workflow uses `kubectl set image` and `kubectl rollout status` against configured deployment/container names.

## GitHub Actions Configuration

### Required repository secrets (Compose path)

- `DEPLOY_SSH_HOST`
- `DEPLOY_SSH_USER`
- `DEPLOY_SSH_KEY`
- `DEPLOY_SSH_PORT` (optional, defaults to 22)
- `DEPLOY_PATH` (absolute path on remote host where repo is deployed)
- `DEPLOY_REGISTRY_USER`
- `DEPLOY_REGISTRY_PASSWORD`

### Required repository secrets (Kubernetes path)

- `KUBE_CONFIG_B64` (base64 encoded kubeconfig)

### Required repository secrets (post-deploy smoke checks)

- `DEPLOY_BASE_URL` (for example, `https://obelisk.example.com`)
- `SMOKE_AUTH_USERNAME` (optional, defaults to `admin`)
- `SMOKE_AUTH_PASSWORD` (optional, defaults to `change_me`)

### Required repository variables

- `DEPLOY_TARGET`: `compose` or `k8s`

Optional Kubernetes variables:

- `K8S_NAMESPACE` (default: `obelisk`)
- `K8S_BACKEND_DEPLOYMENT` (default: `obelisk-backend`)
- `K8S_FRONTEND_DEPLOYMENT` (default: `obelisk-frontend`)
- `K8S_BACKEND_CONTAINER` (default: `backend`)
- `K8S_FRONTEND_CONTAINER` (default: `frontend`)

## Deployment Workflow Execution

### Trigger on merge to main

Any push to `main` triggers the deploy workflow.

### Manual workflow dispatch

The deploy workflow supports:

- `deploy_target`: `compose` or `k8s`
- `image_tag`: optional immutable tag override

If `image_tag` is not provided, the workflow uses the commit SHA.

### One-step repository setup helper

Use `scripts/configure_deploy_workflow.sh` to set required GitHub secrets/variables and optionally dispatch a deployment.

Example:

```bash
export DEPLOY_SSH_HOST="your-host"
export DEPLOY_SSH_USER="deploy"
export DEPLOY_SSH_KEY="$(cat ~/.ssh/id_rsa)"
export DEPLOY_PATH="/srv/obelisk"
export DEPLOY_REGISTRY_USER="your-ghcr-user"
export DEPLOY_REGISTRY_PASSWORD="your-ghcr-token"
export DEPLOY_BASE_URL="https://obelisk.example.com"
export SMOKE_AUTH_USERNAME="admin"
export SMOKE_AUTH_PASSWORD="your-smoke-password"
export DEPLOY_TARGET="compose"

./scripts/configure_deploy_workflow.sh --repo OWNER/REPO --dispatch
```

## Runtime Readiness and Health Gates

Deployment and CI readiness checks validate:

1. Model artifacts:
	- `ml_models/saved_models/codebert/config.json`
	- `ml_models/saved_models/gnn/model.pt`
	- `ml_models/saved_models/isolation_forest/model.joblib`
2. Dependency readiness:
	- PostgreSQL
	- Redis
	- Neo4j

Health endpoints:

- Liveness: `GET /health`
- Readiness: `GET /health/ready`

Readiness returns `503` when degraded.

## Smoke Checks (Hard Gate)

After rollout, deployment is considered successful only if smoke checks pass:

1. `GET /health`
2. `GET /health/ready`
3. `POST /api/auth/login`
4. `GET /api/packages/list`
5. `POST /api/packages/analyze`

## Analyze Flow Quality Gates (CI)

Backend CI enforces the following hard gates:

1. Startup readiness script: `backend/scripts/check_startup_readiness.py`
2. Test suite with coverage fail-under threshold from `backend/pytest.ini`
3. Critical endpoint smoke script: `backend/scripts/smoke_endpoints.py`
4. Analyze latency gate: `backend/scripts/benchmark_analyze.py --mode e2e`

## Sandbox Scope Decision

Sandbox execution is explicitly scoped to v1.1 and excluded from the current critical scoring flow.

- Default mode returns a scoped response (`mode=scoped_v1_1`).
- Optional runtime toggles exist for future activation:
  - `SANDBOX_ENABLED`
  - `SANDBOX_ALLOW_DOCKER`
  - `SANDBOX_RELEASE_TRACK`

## Required Environment and Secrets

At minimum:

- `SECRET_KEY`
- `AUTH_USERNAME`
- `AUTH_PASSWORD`
- `POSTGRES_PASSWORD`
- `NEO4J_PASSWORD`

## Production Hardening Checklist

- Use TLS for all ingress traffic.
- Set `DEBUG=false`.
- Restrict CORS origins to known frontend domains.
- Use strong random secret values.
- Rotate credentials on schedule.
- Pin images by tag or digest.
- Enable vulnerability scans in CI/CD.

## Rollback Strategy

- Keep previous image tags available.
- Keep DB migrations backward compatible when feasible.
- Maintain versioned ML artifact manifests and release pointers.
- Roll back app and model versions together if detector behavior regresses.

Detailed rollback procedures (application, model, and migration) are documented in `docs/OPERATIONS_RUNBOOK.md`.
