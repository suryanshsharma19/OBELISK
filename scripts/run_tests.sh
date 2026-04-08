#!/bin/bash
# run_tests.sh — Run the full test suite (backend + frontend)
# Usage: ./scripts/run_tests.sh [backend|frontend|all]

set -euo pipefail

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
error() { echo -e "${RED}[FAIL]${NC} $*"; }

TARGET=${1:-all}
EXIT_CODE=0

# ---------- Backend Tests ----------
run_backend_tests() {
  info "Running backend tests"
  cd backend

  if [ -d ".venv" ]; then
    source .venv/bin/activate
  fi

  # Run pytest with coverage
  python -m pytest tests/ \
    -v \
    --tb=short \
    --cov=app \
    --cov-config=.coveragerc \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=80 \
    --asyncio-mode=auto || EXIT_CODE=1

  if [ "$EXIT_CODE" -eq 0 ]; then
    info "Backend tests passed"
  else
    error "Backend tests failed"
  fi

  deactivate 2>/dev/null || true
  cd ..
}

# ---------- Frontend Tests ----------
run_frontend_tests() {
  info "Running frontend tests"
  cd frontend

  npx react-scripts test --watchAll=false --coverage || EXIT_CODE=1

  if [ "$EXIT_CODE" -eq 0 ]; then
    info "Frontend tests passed"
  else
    error "Frontend tests failed"
  fi

  cd ..
}

# ---------- Main ----------
case $TARGET in
  backend)
    run_backend_tests
    ;;
  frontend)
    run_frontend_tests
    ;;
  all)
    run_backend_tests
    run_frontend_tests
    ;;
  *)
    echo "Usage: $0 [backend|frontend|all]"
    exit 1
    ;;
esac

if [ "$EXIT_CODE" -eq 0 ]; then
  info "All tests passed!"
else
  error "Some tests failed (exit code $EXIT_CODE)"
fi

exit $EXIT_CODE
