# ML Release Checklist

This checklist enforces production readiness for OBELISK model releases.

## 1. Training and Evaluation

- [x] Run full training pipeline:
  - `python backend/ml_models/train/run_pipeline.py`
  - Or: `make ml-pipeline`
- [x] Confirm benchmark report updated:
  - `backend/ml_models/saved_models/realistic_leaderboard.json`
  - `backend/ml_models/saved_models/realistic_leaderboard.md`

## 2. Acceptance Gates

- [x] Verify model gates pass:
  - `python backend/ml_models/train/check_model_gates.py`
  - Or: `make ml-gates`
- [x] Ensure thresholds are tracked in:
  - `backend/ml_models/train/model_acceptance_gates.yaml`

## 3. Artifact Versioning and Auditability

- [x] Generate versioned artifact manifest:
  - `python backend/ml_models/train/version_artifacts.py`
  - Or: `make ml-version`
- [x] Confirm release metadata exists:
  - `backend/ml_models/saved_models/releases/latest.json`
  - `backend/ml_models/saved_models/releases/<release_id>/manifest.json`

Latest validated release at time of this update:

- `backend/ml_models/saved_models/releases/20260408T123802Z/manifest.json`
- `backend/ml_models/saved_models/releases/latest.json`

## 4. HuggingFace Model Sync

- [x] Push updated models to HuggingFace:
  - `make sync-models`
  - Or: `cd backend && python scripts/upload_models.py`
- [x] Verify models are accessible from HuggingFace:
  - Repository: [`suryanshsharma19/obelisk-models`](https://huggingface.co/suryanshsharma19/obelisk-models)
- [x] Verify `make setup` auto-downloads models on a clean environment:
  - `cd backend && python scripts/download_models.py --force`

## 5. Runtime Validation

- [x] Verify runtime model loading through backend startup smoke tests.
- [x] Verify critical API paths return valid analysis responses.
- [x] Test all 5 detection layers fire during analysis:
  - Typosquatting (Levenshtein heuristics)
  - Code Analysis (CodeBERT transformer)
  - Behavioral (sandbox profiling)
  - Maintainer (Isolation Forest)
  - Dependency (GNN + Neo4j)

## 6. Operational Sign-off

- [x] Commit benchmark + manifest updates.
- [x] Attach benchmark summary and gate output to release PR.
- [x] Record regression notes and rollback artifact reference.

Release sign-off ownership and final go/no-go criteria are tracked in:

- `docs/RELEASE_CHECKLIST.md`
- `docs/SUPPORTABILITY.md`

## Sign-off Notes

- Model gates run result: all configured thresholds passed.
- Artifact versioning command generated and updated release manifest pointer.
- Models synced to HuggingFace: `suryanshsharma19/obelisk-models` (~3.7 GB).
- Rollback reference: use prior manifest in `backend/ml_models/saved_models/releases/` and update `latest.json` atomically.
