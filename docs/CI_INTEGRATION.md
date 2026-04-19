# CI Integration Guide

This guide explains how to use OBELISK as a dependency security gate in external GitHub repositories.

## What This Provides

- A local CLI scanner for CI runners: `scripts/obelisk_ci_scan.py`
- A reusable GitHub Action: `.github/actions/obelisk-dependency-scan/action.yml`
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
  --output-json obelisk-scan-report.json
```

Optional flags:

- `--no-include-dev-dependencies` (dev dependencies are scanned by default)
- `--no-fail-on-unresolved`
- `--no-fail-on-scan-error`
- `--no-mark-blocked-in-ci`

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

      - name: OBELISK dependency scan
        uses: suryanshsharma19/OBELISK/.github/actions/obelisk-dependency-scan@main
        with:
          api_base_url: ${{ secrets.OBELISK_API_BASE_URL }}
          auth_username: ${{ secrets.OBELISK_AUTH_USERNAME }}
          auth_password: ${{ secrets.OBELISK_AUTH_PASSWORD }}
          risk_threshold: "60"
          block_threat_levels: high,critical
          include_dev_dependencies: "true"
          fail_on_unresolved: "true"
          mark_blocked_in_ci: "true"
```

For a runnable in-repo example, see:

- `.github/workflows/obelisk-scan-example.yml`

## Recommended External Repository Secrets

- `OBELISK_API_BASE_URL`
- `OBELISK_AUTH_USERNAME`
- `OBELISK_AUTH_PASSWORD`

## Notes

- For deterministic and scalable CI scans, keep dependency lockfiles committed.
- `blocked_in_ci` marking requires that analyzed packages have associated alerts.
- For private OBELISK deployments, ensure network access from runners to the API endpoint.
