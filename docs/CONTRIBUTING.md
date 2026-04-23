# CONTRIBUTING

## Contribution Principles

OBELISK is a security-focused project. Every contribution should improve correctness, observability, maintainability, or detection quality.

## Workflow

1. Fork/branch from `main`.
2. Keep changes scoped to a single intent.
3. Add tests for every behavioral change.
4. Run local quality checks before opening PR.

## CI Gates On PRs And Commits

OBELISK uses CI gates on both pull requests and commits:

- Backend checks (`.github/workflows/backend-tests.yml`)
- Frontend checks (`.github/workflows/frontend-tests.yml`)
- OBELISK security scan gate (`.github/workflows/obelisk-scan-example.yml`)

For protected branches, merge should be blocked until required checks pass.
See `docs/CI_INTEGRATION.md` for setup details, required secrets, and policy tuning.

## Local Checks Before PR

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm test -- --watchAll=false
npm run build
```

Required backend runtime safety checks:

```bash
cd backend
python scripts/verify_runtime_security.py --strict
python scripts/check_startup_readiness.py --strict --include-dependencies
python scripts/smoke_endpoints.py
```

CI additionally enforces `python scripts/verify_runtime_security.py --strict --require-non-local`.

Dependency guidance for CI scan reliability:

- Commit lockfiles (`package-lock.json`, `poetry.lock`, `Pipfile.lock`) when dependencies change.
- Prefer exact versions in `requirements*.txt` (`==` or `===`) to avoid unresolved-scan failures.

Performance gate:

```bash
cd backend
python scripts/benchmark_analyze.py --mode e2e --samples 40 --warmup 10 --enforce-under-ms 250
```

## Code Standards

- Prefer clear, typed interfaces in Python.
- Keep route handlers lightweight; move logic to services.
- Ensure errors are explicit and logged.
- Avoid breaking response contracts without migration notes.
- For frontend, keep components focused and test critical user paths.

## ML Model Contributions

If your changes affect ML detectors or training pipelines:

1. Train and evaluate models: `make ml-pipeline`
2. Verify acceptance gates pass: `make ml-gates`
3. Run the adversarial malware test suite: `make adversarial-check`
4. Push updated models to HuggingFace: `make sync-models`
5. Include benchmark results in your PR description.

## Pull Request Checklist

- [ ] Change description and motivation are clear.
- [ ] Risk impact is documented (security/performance/compatibility).
- [ ] Test evidence is included.
- [ ] Any schema or API change is documented.
- [ ] Backward compatibility notes are included where required.
- [ ] ML model changes include updated benchmarks and HuggingFace sync.

## Security Reporting

Do not open public issues for exploitable vulnerabilities. Coordinate through maintainers and provide reproducible details privately.
