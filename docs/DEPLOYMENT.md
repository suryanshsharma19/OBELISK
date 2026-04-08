# DEPLOYMENT

## Deployment Targets

OBELISK supports:

1. Docker Compose (single-host/dev).
2. Kubernetes (production-style orchestration).
3. Terraform-backed infrastructure provisioning.

## Docker Compose Deployment

```bash
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
docker-compose up -d --build
```

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
