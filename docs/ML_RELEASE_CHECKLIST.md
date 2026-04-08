# ML Release Checklist

This checklist enforces production readiness for OBELISK model releases.

## 1. Training and Evaluation

- [x] Run full training pipeline:
  - `python backend/ml_models/train/run_pipeline.py`
- [x] Confirm benchmark report updated:
  - `backend/ml_models/saved_models/realistic_leaderboard.json`
  - `backend/ml_models/saved_models/realistic_leaderboard.md`

## 2. Acceptance Gates

- [x] Verify model gates pass:
  - `python backend/ml_models/train/check_model_gates.py`
- [x] Ensure thresholds are tracked in:
  - `backend/ml_models/train/model_acceptance_gates.yaml`

## 3. Artifact Versioning and Auditability

- [x] Generate versioned artifact manifest:
  - `python backend/ml_models/train/version_artifacts.py`
- [x] Confirm release metadata exists:
  - `backend/ml_models/saved_models/releases/latest.json`
  - `backend/ml_models/saved_models/releases/<release_id>/manifest.json`

Latest validated release at time of this update:

- `backend/ml_models/saved_models/releases/20260408T123802Z/manifest.json`
- `backend/ml_models/saved_models/releases/latest.json`

## 4. Runtime Validation

- [x] Verify runtime model loading through backend startup smoke tests.
- [x] Verify critical API paths return valid analysis responses.

## 5. Operational Sign-off

- [x] Commit benchmark + manifest updates.
- [x] Attach benchmark summary and gate output to release PR.
- [x] Record regression notes and rollback artifact reference.

## Sign-off Notes

- Model gates run result: all configured thresholds passed.
- Artifact versioning command generated and updated release manifest pointer.
- Rollback reference: use prior manifest in `backend/ml_models/saved_models/releases/` and update `latest.json` atomically.
