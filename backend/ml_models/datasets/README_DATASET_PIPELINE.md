# OBELISK Dataset Pipeline

This pipeline retrieves and normalizes datasets for all OBELISK model families.

## What it builds

- Unified file: `processed/unified/unified_samples.jsonl`
- CodeBERT dataset: `processed/codebert/dataset.csv`
- Isolation Forest dataset: `processed/maintainers/maintainer_features.csv`
- GNN dataset directory: `processed/dependency_graphs/*.json`
- Summary: `processed/unified/summary.json`

## Sources integrated

- Backstabbers Knife Collection
- npm security advisories repository
- GitHub advisory database
- python-supply-chain-attacks repository
- npm registry metadata and package source snapshots
- PyPI metadata and package source snapshots
- Synthetic augmentation samples

Large optional sources can be added through the manual drop-zone:

- `backend/ml_models/datasets/raw/manual/codesearchnet/` for CodeSearchNet json/jsonl files
- `backend/ml_models/datasets/raw/manual/librariesio/dependencies.csv` for Libraries.io dependency export
- `backend/ml_models/datasets/raw/manual/malwaresourcecode/` for malware source snapshots

## Run commands

From repository root:

```bash
make datasets-quick
```

For larger collection:

```bash
make datasets
```

Offline rebuild from already-downloaded raw cache:

```bash
make datasets-offline
```

## Environment notes

- `git` is required for repository-based sources.
- `npm` is required for npm package source snapshots.
- `python3 -m pip` is required for PyPI source snapshots. If pip is unavailable, PyPI metadata is still collected for anomaly and graph datasets.

## Direct script usage

```bash
python3 backend/ml_models/datasets/collect_and_prepare.py \
  --max-npm-malicious 300 \
  --max-npm-benign 300 \
  --max-pypi-malicious 300 \
  --max-pypi-benign 300 \
  --synthetic-code-samples 1000
```

## Feeding to training scripts

CodeBERT:

```bash
python3 backend/ml_models/train/train_codebert.py \
  --dataset backend/ml_models/datasets/processed/codebert/dataset.csv \
  --output backend/ml_models/saved_models/codebert
```

Isolation Forest:

```bash
python3 backend/ml_models/train/train_isolation_forest.py \
  --dataset backend/ml_models/datasets/processed/maintainers/maintainer_features.csv \
  --output backend/ml_models/saved_models/isolation_forest
```

GNN:

```bash
python3 backend/ml_models/train/train_gnn.py \
  --dataset backend/ml_models/datasets/processed/dependency_graphs \
  --output backend/ml_models/saved_models/gnn
```

## Safety notes

- The pipeline downloads and parses source code as text and metadata only.
- It does not execute downloaded package code.
- Keep malware-related raw sources in isolated environments and do not run unknown scripts.
