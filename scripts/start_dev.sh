#!/bin/bash
# start_dev.sh — Start all services in development mode
# Usage: ./scripts/start_dev.sh

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $*"; }

# Track PIDs so we can clean up on Ctrl-C
PIDS=()

cleanup() {
  info "Shutting down..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  # Stop docker containers if we started them
  docker compose down 2>/dev/null || true
  exit 0
}

trap cleanup SIGINT SIGTERM

# ---------- Infrastructure ----------
if command -v docker >/dev/null 2>&1; then
  info "Starting infrastructure (Postgres, Neo4j, Redis)"
  docker compose up -d postgres neo4j redis
  sleep 3
else
  warn "Docker not found — ensure databases are running manually"
fi

# ---------- Backend ----------
info "Starting backend (FastAPI on port 8000)"
cd backend
if [ -d ".venv" ]; then
  source .venv/bin/activate
fi

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
PIDS+=("$!")
cd ..

# ---------- Frontend ----------
info "Starting frontend (React on port 3000)"
cd frontend
npm start &
PIDS+=("$!")
cd ..

info "Development servers started:"
info "  Backend:  http://localhost:8000"
info "  Frontend: http://localhost:3000"
info "  Neo4j:    http://localhost:7474"
info "Press Ctrl+C to stop all services."

# Wait for all background processes
wait
