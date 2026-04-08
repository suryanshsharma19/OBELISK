# API

This document describes the currently implemented OBELISK backend API.

## Base

- Local URL: `http://localhost:8000`
- Auth type: Bearer JWT (`Authorization: Bearer <token>`)
- Interactive docs:
	- Swagger UI: `/docs`
	- ReDoc: `/redoc`

## Authentication

### POST /api/auth/login

Request body:

```json
{
	"username": "admin",
	"password": "change_me"
}
```

Response:

```json
{
	"access_token": "<jwt>",
	"token_type": "bearer",
	"expires_in": 3600,
	"user": {"username": "admin"}
}
```

### POST /api/auth/logout

Clears auth cookie. Returns `{ "status": "ok" }`.

### GET /api/auth/me

Returns authenticated username:

```json
{
	"user": {"username": "admin"}
}
```

## Health

### GET /health

Public endpoint for health probes.

## Package Analysis

### POST /api/packages/analyze

Protected endpoint. Runs full analysis pipeline.

Request body:

```json
{
	"name": "express",
	"version": "4.18.2",
	"registry": "npm",
	"code": "module.exports = ..."
}
```

Response shape:

```json
{
	"package": {"name": "express", "version": "4.18.2", "registry": "npm"},
	"analysis": {"risk_score": 12.3, "threat_level": "low", "is_malicious": false},
	"detection_details": {}
}
```

### GET /api/packages/list

Protected endpoint. Supports pagination and filtering.

Query params:

- `skip` (default `0`)
- `limit` (default `50`, max `100`)
- `threat_level` (optional)
- `registry` (optional)
- `sort` (`analyzed_at_desc`, `analyzed_at_asc`, `risk_score_desc`, `risk_score_asc`)

### GET /api/packages/{package_id}

Protected endpoint. Returns package summary, latest analysis, and recent alerts.

## Alerts

### GET /api/alerts/

Protected endpoint with query params:

- `skip`, `limit`
- `threat_level` (optional)
- `is_resolved` (optional)

### GET /api/alerts/{alert_id}

Protected endpoint. Returns full alert details.

### PUT /api/alerts/{alert_id}

Protected endpoint. Optional query params:

- `is_read`
- `is_resolved`
- `registry_reported`
- `blocked_in_ci`

### POST /api/alerts/bulk?action=mark_read|resolve|report

Protected endpoint. Body is a JSON array of alert IDs.

## Statistics

### GET /api/stats/overview

Protected endpoint. Returns dashboard counters and threat distribution.

### GET /api/stats/trend?days=7

Protected endpoint. Returns date-wise trend points.

## Registry Crawler

### POST /api/crawler/start

Starts crawler state machine in current runtime.

### POST /api/crawler/stop

Stops crawler state machine in current runtime.

### GET /api/crawler/status

Returns crawler state and counters.

## WebSocket

### WS /ws

Protected endpoint. Auth token can be provided through:

- `Authorization` header, or
- `?token=<jwt>` query parameter.

Client heartbeat:

- Send: `{"type":"ping"}`
- Receive: `{"type":"pong"}`

## Error Contract

Typical JSON error payload:

```json
{
	"detail": "error message"
}
```

Global unhandled errors are normalized to:

```json
{
	"error": "InternalServerError",
	"message": "An unexpected error occurred. Please try again later."
}
```
