#!/usr/bin/env bash
# Configure GitHub Actions deploy workflow secrets/variables and optionally dispatch a deployment.
#
# Usage:
#   export DEPLOY_SSH_HOST=...
#   export DEPLOY_SSH_USER=...
#   export DEPLOY_SSH_KEY="$(cat ~/.ssh/id_rsa)"
#   export DEPLOY_PATH=/srv/obelisk
#   export DEPLOY_REGISTRY_USER=...
#   export DEPLOY_REGISTRY_PASSWORD=...
#   export DEPLOY_BASE_URL=https://obelisk.example.com
#   export SMOKE_AUTH_USERNAME=admin
#   export SMOKE_AUTH_PASSWORD=...
#   export DEPLOY_TARGET=compose
#   ./scripts/configure_deploy_workflow.sh --repo suryanshsharma19/OBELISK --dispatch
#
# Optional Kubernetes secrets/vars:
#   export KUBE_CONFIG_B64="$(base64 -w0 ~/.kube/config)"
#   export K8S_NAMESPACE=obelisk
#   export K8S_BACKEND_DEPLOYMENT=obelisk-backend
#   export K8S_FRONTEND_DEPLOYMENT=obelisk-frontend
#   export K8S_BACKEND_CONTAINER=backend
#   export K8S_FRONTEND_CONTAINER=frontend

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

usage() {
  cat <<'EOF'
Configure deploy workflow secrets/variables in GitHub Actions.

Options:
  --repo OWNER/REPO   GitHub repository (defaults to origin remote)
  --dispatch          Trigger deploy workflow after config
  --image-tag TAG     Optional image_tag input for manual dispatch
  --help              Show this help message
EOF
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || error "Required command not found: $1"
}

infer_repo_from_origin() {
  local remote_url
  remote_url="$(git remote get-url origin 2>/dev/null || true)"
  if [[ -z "$remote_url" ]]; then
    return 1
  fi

  # Supports:
  #   https://github.com/owner/repo.git
  #   git@github.com:owner/repo.git
  remote_url="${remote_url%.git}"
  if [[ "$remote_url" =~ github\.com[:/]([^/]+/[^/]+)$ ]]; then
    printf '%s\n' "${BASH_REMATCH[1]}"
    return 0
  fi
  return 1
}

set_secret() {
  local repo="$1"
  local name="$2"
  local value="$3"

  if [[ -z "$value" ]]; then
    error "Missing required secret value for $name"
  fi

  printf '%s' "$value" | gh secret set "$name" -R "$repo" -b-
  info "Set secret: $name"
}

set_variable_if_present() {
  local repo="$1"
  local name="$2"
  local value="$3"

  if [[ -z "$value" ]]; then
    warn "Variable not set (skipped): $name"
    return 0
  fi

  gh variable set "$name" -R "$repo" --body "$value"
  info "Set variable: $name=$value"
}

REPO=""
DISPATCH="0"
IMAGE_TAG=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo)
      REPO="$2"
      shift 2
      ;;
    --dispatch)
      DISPATCH="1"
      shift
      ;;
    --image-tag)
      IMAGE_TAG="$2"
      shift 2
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      error "Unknown option: $1"
      ;;
  esac
done

require_cmd gh
require_cmd git

gh auth status >/dev/null 2>&1 || error "gh is not authenticated. Run: gh auth login"

if [[ -z "$REPO" ]]; then
  REPO="$(infer_repo_from_origin || true)"
fi
[[ -n "$REPO" ]] || error "Could not infer repository; pass --repo OWNER/REPO"

info "Configuring deploy workflow for repo: $REPO"

# Required secrets for compose + smoke checks.
set_secret "$REPO" "DEPLOY_SSH_HOST" "${DEPLOY_SSH_HOST:-}"
set_secret "$REPO" "DEPLOY_SSH_USER" "${DEPLOY_SSH_USER:-}"
set_secret "$REPO" "DEPLOY_SSH_KEY" "${DEPLOY_SSH_KEY:-}"
set_secret "$REPO" "DEPLOY_PATH" "${DEPLOY_PATH:-}"
set_secret "$REPO" "DEPLOY_REGISTRY_USER" "${DEPLOY_REGISTRY_USER:-}"
set_secret "$REPO" "DEPLOY_REGISTRY_PASSWORD" "${DEPLOY_REGISTRY_PASSWORD:-}"
set_secret "$REPO" "DEPLOY_BASE_URL" "${DEPLOY_BASE_URL:-}"
set_secret "$REPO" "SMOKE_AUTH_USERNAME" "${SMOKE_AUTH_USERNAME:-}"
set_secret "$REPO" "SMOKE_AUTH_PASSWORD" "${SMOKE_AUTH_PASSWORD:-}"

# Optional compose secret.
if [[ -n "${DEPLOY_SSH_PORT:-}" ]]; then
  set_secret "$REPO" "DEPLOY_SSH_PORT" "${DEPLOY_SSH_PORT}"
fi

# Optional Kubernetes secret.
if [[ -n "${KUBE_CONFIG_B64:-}" ]]; then
  set_secret "$REPO" "KUBE_CONFIG_B64" "${KUBE_CONFIG_B64}"
else
  warn "KUBE_CONFIG_B64 not set (k8s deploy target will not work until configured)"
fi

# Required workflow variable.
set_variable_if_present "$REPO" "DEPLOY_TARGET" "${DEPLOY_TARGET:-compose}"

# Optional Kubernetes variables.
set_variable_if_present "$REPO" "K8S_NAMESPACE" "${K8S_NAMESPACE:-}"
set_variable_if_present "$REPO" "K8S_BACKEND_DEPLOYMENT" "${K8S_BACKEND_DEPLOYMENT:-}"
set_variable_if_present "$REPO" "K8S_FRONTEND_DEPLOYMENT" "${K8S_FRONTEND_DEPLOYMENT:-}"
set_variable_if_present "$REPO" "K8S_BACKEND_CONTAINER" "${K8S_BACKEND_CONTAINER:-}"
set_variable_if_present "$REPO" "K8S_FRONTEND_CONTAINER" "${K8S_FRONTEND_CONTAINER:-}"

if [[ "$DISPATCH" == "1" ]]; then
  DEPLOY_TARGET_INPUT="${DEPLOY_TARGET:-compose}"
  info "Dispatching deploy workflow (target=${DEPLOY_TARGET_INPUT}, image_tag=${IMAGE_TAG:-<sha-default>})"

  if [[ -n "$IMAGE_TAG" ]]; then
    gh workflow run deploy.yml -R "$REPO" -f deploy_target="$DEPLOY_TARGET_INPUT" -f image_tag="$IMAGE_TAG"
  else
    gh workflow run deploy.yml -R "$REPO" -f deploy_target="$DEPLOY_TARGET_INPUT"
  fi

  info "Deployment workflow dispatched"
  info "Recent runs:"
  gh run list -R "$REPO" --workflow deploy.yml --limit 5
fi

info "Deploy workflow configuration completed"
