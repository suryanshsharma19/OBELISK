#!/bin/bash
# deploy.sh — Build and deploy OBELISK to production
# Usage: ./scripts/deploy.sh [--env staging|production]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

ENV="production"
REGISTRY="ghcr.io/obelisk"
TAG=$(git describe --tags --always 2>/dev/null || echo "latest")

while [[ $# -gt 0 ]]; do
  case $1 in
    --env) ENV="$2"; shift 2 ;;
    *) shift ;;
  esac
done

info "Deploying OBELISK (env=$ENV, tag=$TAG)"

# ---------- Pre-flight ----------
command -v docker >/dev/null 2>&1 || error "docker is required"

# ---------- Run tests first ----------
info "Running test suite"
./scripts/run_tests.sh backend || error "Tests failed — deploy aborted"

# ---------- Build Docker images ----------
info "Building backend image"
docker build -t "$REGISTRY/backend:$TAG" -f backend/Dockerfile backend/

info "Building frontend image"
docker build -t "$REGISTRY/frontend:$TAG" -f frontend/Dockerfile frontend/

# ---------- Push images ----------
info "Pushing images to registry"
docker push "$REGISTRY/backend:$TAG"
docker push "$REGISTRY/frontend:$TAG"

# ---------- Deploy ----------
if [ "$ENV" = "production" ]; then
  info "Deploying to production with docker compose"
  COMPOSE_FILE="infrastructure/docker/docker-compose.prod.yml"

  TAG=$TAG docker compose -f "$COMPOSE_FILE" pull
  TAG=$TAG docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

  info "Running database migrations"
  docker compose -f "$COMPOSE_FILE" exec backend alembic upgrade head
else
  info "Deploying to staging"
  COMPOSE_FILE="docker-compose.yml"
  TAG=$TAG docker compose -f "$COMPOSE_FILE" up -d --build
fi

# ---------- Health check ----------
info "Waiting for services to start"
sleep 10

if curl -sf http://localhost:8000/health > /dev/null; then
  info "Health check passed"
else
  error "Health check failed — check logs with: docker compose logs"
fi

info "Deployment complete (env=$ENV, tag=$TAG)"
