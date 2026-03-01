#!/bin/bash
# monitoring.sh — Check health of all OBELISK services
# Usage: ./scripts/monitoring.sh [--loop]

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

OK()   { echo -e "  ${GREEN}\u2713${NC} $*"; }
FAIL() { echo -e "  ${RED}\u2717${NC} $*"; }

LOOP=false
[[ "${1:-}" = "--loop" ]] && LOOP=true

check_services() {
  echo "=== OBELISK Service Health Check ==="
  echo "$(date)"
  echo

  # Backend API
  if curl -sf --max-time 5 http://localhost:8000/health > /dev/null 2>&1; then
    OK "Backend API — healthy"
  else
    FAIL "Backend API — unreachable"
  fi

  # Frontend
  if curl -sf --max-time 5 http://localhost:3000 > /dev/null 2>&1; then
    OK "Frontend — serving"
  else
    FAIL "Frontend — unreachable"
  fi

  # PostgreSQL
  if pg_isready -h localhost -p 5432 -q 2>/dev/null; then
    OK "PostgreSQL — accepting connections"
  elif docker compose exec -T postgres pg_isready -q 2>/dev/null; then
    OK "PostgreSQL (Docker) — accepting connections"
  else
    FAIL "PostgreSQL — not reachable"
  fi

  # Redis
  if redis-cli -h localhost -p 6379 ping 2>/dev/null | grep -q PONG; then
    OK "Redis — responding"
  elif docker compose exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
    OK "Redis (Docker) — responding"
  else
    FAIL "Redis — not reachable"
  fi

  # Neo4j
  if curl -sf --max-time 5 http://localhost:7474 > /dev/null 2>&1; then
    OK "Neo4j — browser available"
  else
    FAIL "Neo4j — not reachable"
  fi

  # Docker container status
  echo
  echo "Container Status:"
  docker compose ps --format 'table {{.Name}}\t{{.Status}}' 2>/dev/null || echo "  Docker compose not available"

  echo
  echo "Disk Usage:"
  df -h / | tail -1 | awk '{ printf "  Total: %s  Used: %s  Free: %s  (%s)\n", $2, $3, $4, $5 }'

  echo
  echo "Memory:"
  free -h 2>/dev/null | awk 'NR==2 { printf "  Total: %s  Used: %s  Free: %s\n", $2, $3, $4 }' || echo "  (not available)"

  echo "-------------------------------"
}

if $LOOP; then
  while true; do
    check_services
    sleep 30
  done
else
  check_services
fi
