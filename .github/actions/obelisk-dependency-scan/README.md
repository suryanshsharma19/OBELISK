# OBELISK Dependency Scan Action

Reusable composite GitHub Action for scanning dependencies with OBELISK.

## Inputs

- `api_base_url` (required)
- `auth_username` (required)
- `auth_password` (required)
- `repo_path` (default: `.`)
- `risk_threshold` (default: `60`)
- `block_threat_levels` (default: `high,critical`)
- `include_dev_dependencies` (default: `true`)
- `fail_on_unresolved` (default: `true`)
- `fail_on_scan_error` (default: `true`)
- `mark_blocked_in_ci` (default: `true`)
- `output_json` (default: `obelisk-scan-report.json`)

## Example

```yaml
- name: OBELISK dependency scan
  uses: suryanshsharma19/OBELISK/.github/actions/obelisk-dependency-scan@main
  with:
    api_base_url: ${{ secrets.OBELISK_API_BASE_URL }}
    auth_username: ${{ secrets.OBELISK_AUTH_USERNAME }}
    auth_password: ${{ secrets.OBELISK_AUTH_PASSWORD }}
    risk_threshold: "60"
    block_threat_levels: high,critical
    include_dev_dependencies: "true"
```

The action fails with non-zero exit status when policy blocks a dependency
or when scanning errors occur in strict mode.
