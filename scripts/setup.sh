#!/bin/bash
# setup.sh — First-time project setup (dependencies, DB, env)
# Usage: ./scripts/setup.sh

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---------- Pre-flight checks ----------
command -v python3 >/dev/null 2>&1 || error "python3 is required"
command -v node    >/dev/null 2>&1 || error "node is required"
command -v docker  >/dev/null 2>&1 || warn  "docker not found (optional for dev)"

# ---------- Environment file ----------
if [ ! -f .env ]; then
  info "Creating .env from template"
  cat > .env <<'EOF'
# OBELISK environment variables
DATABASE_URL=postgresql://obelisk:obelisk@localhost:5432/obelisk
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=obelisk_neo4j
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=true
EOF
fi

# ---------- Backend setup ----------
info "Setting up backend"
cd backend

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install --upgrade pip -q
pip install -r requirements.txt -q
pip install -r requirements-dev.txt -q
pip install -e . -q

info "Backend dependencies installed"

# ---------- Database ----------
if command -v docker >/dev/null 2>&1; then
  info "Starting infrastructure containers"
  cd ..
  docker compose up -d postgres neo4j redis
  sleep 5
  cd backend
fi

info "Running database migrations"
python -m alembic upgrade head 2>/dev/null || warn "Migrations skipped (DB not available?)"

info "Seeding sample data"
python scripts/seed_data.py 2>/dev/null || warn "Seeding skipped"

deactivate
cd ..

# ---------- Frontend setup ----------
info "Setting up frontend"
cd frontend
npm install --silent
cd ..

info "Setup complete! Run ./scripts/start_dev.sh to start."
