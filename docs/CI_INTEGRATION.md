# CI Integration Guide

This guide explains how to use OBELISK as a dependency security gate in external GitHub repositories.

## What This Provides

- A local CLI scanner for CI runners: `scripts/obelisk_ci_scan.py`
- A reusable GitHub Action: `.github/actions/obelisk-dependency-scan/action.yml`
- PR/push changed-file code scan from git diff ranges (for example base SHA to head SHA)
- Policy enforcement that fails CI when:
  - `threat_level` is in a blocked set (default: `high,critical`), or
  - `risk_score` is greater than or equal to a threshold (default: `60`)
- Optional alert marking via `blocked_in_ci=true` for related alerts.

## Supported Manifest Resolution

The scanner resolves exact package versions from:

- `package-lock.json`
- `npm-shrinkwrap.json`
- `package.json` (only exact versions; ranges are flagged unresolved)
- `requirements*.txt` (only `==` and `===` pins)
- `Pipfile.lock`
- `poetry.lock`

If a dependency cannot be resolved to an exact version, the scanner records a resolution issue.
By default, unresolved dependencies fail the run (`--fail-on-unresolved`).

## Changed-Code Scan Scope

In addition to dependency manifests, the scanner can analyze changed source files from git diff.

- Enabled by default via `--scan-changed-code`.
- Diff range can be passed explicitly with `--git-diff-range`.
- If omitted, scanner attempts to infer range from CI environment (`pull_request` base ref, push before SHA, or `HEAD~1...HEAD`).
- Only allowed extensions are scanned (default: `.py,.js,.jsx,.ts,.tsx,.mjs,.cjs`).

## Local CLI Usage

Run on any checkout (including external repositories):

```bash
python3 scripts/obelisk_ci_scan.py \
  --repo-path /path/to/target/repo \
  --api-base-url https://obelisk.example.com \
  --auth-username "$OBELISK_AUTH_USERNAME" \
  --auth-password "$OBELISK_AUTH_PASSWORD" \
  --risk-threshold 60 \
  --block-threat-levels high,critical \
  --scan-changed-code \
  --git-diff-range "$BASE_SHA...$HEAD_SHA" \
  --output-json obelisk-scan-report.json
```

Optional flags:

- `--no-include-dev-dependencies` (dev dependencies are scanned by default)
- `--no-scan-changed-code`
- `--no-fail-on-unresolved`
- `--no-fail-on-scan-error`
- `--no-mark-blocked-in-ci`
- `--allowed-code-extensions`
- `--max-changed-files`
- `--max-code-file-bytes`
- `--max-code-chars`

Exit codes:

- `0` success
- `1` blocked by policy
- `2` scan/API error
- `3` unresolved dependency versions with strict mode enabled

## Reusable GitHub Action Usage

From an external repository workflow:

```yaml
name: Dependency Security Gate
on:
  pull_request:
  push:
    branches: [main]

jobs:
  obelisk-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Resolve diff range
        id: diff
        run: |
          echo "range=${{ github.event.pull_request.base.sha }}...${{ github.event.pull_request.head.sha }}" >> "$GITHUB_OUTPUT"

      - name: OBELISK dependency scan
        uses: suryanshsharma19/OBELISK/.github/actions/obelisk-dependency-scan@main
        with:
          api_base_url: ${{ secrets.OBELISK_API_BASE_URL }}
          auth_username: ${{ secrets.OBELISK_AUTH_USERNAME }}
          auth_password: ${{ secrets.OBELISK_AUTH_PASSWORD }}
          risk_threshold: "60"
          block_threat_levels: high,critical
          include_dev_dependencies: "true"
          scan_changed_code: "true"
          git_diff_range: ${{ steps.diff.outputs.range }}
          fail_on_unresolved: "true"
          mark_blocked_in_ci: "true"
```

For a runnable in-repo example, see:

- `.github/workflows/obelisk-scan-example.yml`

## Recommended External Repository Secrets

- `OBELISK_API_BASE_URL`
- `OBELISK_AUTH_USERNAME`
- `OBELISK_AUTH_PASSWORD`

## Using This Feature In The OBELISK Repository

This repository already includes a workflow that demonstrates PR/commit security gating:

- `.github/workflows/obelisk-scan-example.yml`

It runs on:

- `pull_request`
- `push` to `main`

### 1. Configure scanner secrets

In GitHub repository settings, add:

- `OBELISK_API_BASE_URL`
- `OBELISK_AUTH_USERNAME`
- `OBELISK_AUTH_PASSWORD`

Without these secrets, the example workflow logs a skip message and does not execute the scan step.

### 2. Trigger on PR or commit

Create a pull request or push a commit to `main`. The workflow resolves git diff range and scans:

- Dependency manifests and lockfiles
- Changed code files from git diff

### 3. Read results

Open the workflow run and inspect:

- Job status (`passed`, `blocked`, or `failed`)
- Uploaded artifact `obelisk-scan-report` for full JSON output

### 4. Enforce before merge (required checks)

To make this a hard pre-merge gate:

1. Go to branch protection rules for `main`.
2. Enable required status checks.
3. Mark at least these checks as required:
  - `Backend Tests / test`
  - `Frontend Tests / test`
  - `OBELISK Scan Example / dependency-security-gate`

Once required, PRs cannot be merged until all selected checks pass.

### 5. Tune policy

Adjust workflow inputs in `.github/workflows/obelisk-scan-example.yml`:

- `risk_threshold`
- `block_threat_levels`
- `fail_on_unresolved`
- `fail_on_scan_error`
- `scan_changed_code`

## Notes

- For deterministic and scalable CI scans, keep dependency lockfiles committed.
- `blocked_in_ci` marking requires that analyzed packages have associated alerts.
- For private OBELISK deployments, ensure network access from runners to the API endpoint.
