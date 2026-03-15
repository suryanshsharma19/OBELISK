# SECURITY

## Security Model

OBELISK uses a layered security model aligned with the project bible:

1. Network security: TLS-terminated ingress, HTTPS-only redirect.
2. Authentication: JWT bearer tokens (also set as HttpOnly cookie).
3. Authorization: protected API and WebSocket routes require valid tokens.
4. Input validation: FastAPI + Pydantic request schemas.
5. Application controls: endpoint rate limiting and controlled error responses.
6. Data protection: secrets externalized to environment/Kubernetes Secret.
7. Runtime hardening: non-root containers, dropped Linux capabilities, seccomp.

## Implemented Controls

- Auth endpoints:
	- POST /api/auth/login
	- POST /api/auth/logout
	- GET /api/auth/me
- Protected routes:
	- /api/packages/*
	- /api/alerts/*
	- /api/stats/*
	- /api/crawler/*
	- /ws (requires JWT via query token or Authorization header)
- Security headers:
	- X-Content-Type-Options: nosniff
	- X-Frame-Options: DENY
	- Referrer-Policy: same-origin
	- Permissions-Policy: restrictive defaults

## Secret Management

- Never commit real credentials to git.
- Use .env (local) or secret manager/Kubernetes Secrets (deployment).
- Required secure variables:
	- SECRET_KEY
	- AUTH_PASSWORD
	- POSTGRES_PASSWORD
	- NEO4J_PASSWORD

## Deployment Hardening Checklist

- Replace all REPLACE_WITH_* placeholders before deploy.
- Keep DEBUG disabled in non-local environments.
- Set SECURE_COOKIES=true for HTTPS deployments.
- Restrict CORS_ORIGINS to trusted frontend domains only.
- Use immutable image versions (or digests), not latest.
- Keep ingress TLS certificates valid and rotated.
- Run periodic dependency vulnerability scanning in CI.

## Incident Readiness

- Rotate SECRET_KEY and auth credentials after any suspected compromise.
- Revoke active sessions by rotating SECRET_KEY.
- Review logs and alerts for unusual authentication failure spikes.
