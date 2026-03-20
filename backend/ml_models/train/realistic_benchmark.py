#!/usr/bin/env python3
"""Run realistic multi-seed evaluations with confidence intervals for all models."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
from collections import defaultdict
from pathlib import Path

import joblib
import numpy as np
import torch
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from torch_geometric.loader import DataLoader as GeometricDataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from train_gnn import PackageGCN, load_graph_data, split_graphs_by_family


def metrics_dict(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
    }


def summarize_with_ci(rows: list[dict[str, float]]) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    keys = ["accuracy", "precision", "recall", "f1"]
    n = max(len(rows), 1)
    for key in keys:
        vals = np.array([r[key] for r in rows], dtype=np.float64)
        mean = float(np.mean(vals))
        std = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0
        ci95 = float(1.96 * std / np.sqrt(n)) if len(vals) > 1 else 0.0
        out[key] = {"mean": mean, "std": std, "ci95": ci95}
    return out


def codebert_family(package: str) -> str:
    pkg = package.strip().lower()
    if "/" in pkg:
        pkg = pkg.split("/", 1)[0]
    token = re.split(r"[-_.]", pkg)[0]
    return token or "unknown"


def load_codebert_rows(dataset_csv: Path, exclude_synthetic: bool = True) -> list[tuple[str, int, str]]:
    rows: list[tuple[str, int, str]] = []
    with dataset_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            source = str(row.get("source", ""))
            if exclude_synthetic and source == "synthetic":
                continue
            code = str(row.get("code", "")).strip()
            if len(code) < 40:
                continue
            label = int(row.get("label", 0))
            family = codebert_family(str(row.get("package", "unknown")))
            rows.append((code, label, family))
    return rows


def split_codebert_by_family(rows: list[tuple[str, int, str]], val_ratio: float, seed: int) -> tuple[list, list]:
    rng = random.Random(seed)
    grouped: dict[str, list[tuple[str, int, str]]] = defaultdict(list)
    for row in rows:
        grouped[row[2]].append(row)

    fams = list(grouped.keys())
    rng.shuffle(fams)
    target = max(int(len(rows) * val_ratio), 1)

    train: list[tuple[str, int, str]] = []
    val: list[tuple[str, int, str]] = []
    val_count = 0
    for fam in fams:
        chunk = grouped[fam]
        if val_count < target:
            val.extend(chunk)
            val_count += len(chunk)
        else:
            train.extend(chunk)

    if not train or not val:
        shuffled = list(rows)
        rng.shuffle(shuffled)
        cut = max(int(len(shuffled) * (1.0 - val_ratio)), 1)
        train = shuffled[:cut]
        val = shuffled[cut:]

    return train, val


def evaluate_codebert(model_dir: Path, dataset_csv: Path, seeds: list[int], val_ratio: float) -> tuple[list[dict[str, float]], int]:
    rows = load_codebert_rows(dataset_csv, exclude_synthetic=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir).to(device)
    model.eval()

    per_seed: list[dict[str, float]] = []
    with torch.no_grad():
        for seed in seeds:
            _train, val = split_codebert_by_family(rows, val_ratio=val_ratio, seed=seed)
            y_true: list[int] = []
            y_pred: list[int] = []

            batch_size = 16
            for i in range(0, len(val), batch_size):
                batch = val[i : i + batch_size]
                texts = [x[0] for x in batch]
                labels = [x[1] for x in batch]
                enc = tokenizer(
                    texts,
                    truncation=True,
                    max_length=256,
                    padding=True,
                    return_tensors="pt",
                )
                enc = {k: v.to(device) for k, v in enc.items()}
                logits = model(**enc).logits
                preds = torch.argmax(logits, dim=-1).detach().cpu().tolist()
                y_true.extend(labels)
                y_pred.extend(preds)

            per_seed.append(metrics_dict(y_true, y_pred))

    return per_seed, len(rows)


def evaluate_gnn(model_path: Path, dataset_dir: Path, seeds: list[int], val_ratio: float, hidden_dim: int, dropout: float) -> tuple[list[dict[str, float]], int]:
    graphs = load_graph_data(str(dataset_dir))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PackageGCN(hidden=hidden_dim, dropout=dropout).to(device)
    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state)
    model.eval()

    per_seed: list[dict[str, float]] = []
    with torch.no_grad():
        for seed in seeds:
            _train, val = split_graphs_by_family(graphs, val_ratio=val_ratio, seed=seed)
            loader = GeometricDataLoader(val, batch_size=64)
            y_true: list[int] = []
            y_pred: list[int] = []
            for batch in loader:
                batch = batch.to(device)
                logits = model(batch.x, batch.edge_index, batch.batch)
                preds = logits.argmax(dim=-1).detach().cpu().tolist()
                labels = batch.y.view(-1).detach().cpu().tolist()
                y_true.extend(labels)
                y_pred.extend(preds)
            per_seed.append(metrics_dict(y_true, y_pred))

    return per_seed, len(graphs)


def evaluate_gnn_thresholded(
    model_path: Path,
    dataset_dir: Path,
    seeds: list[int],
    val_ratio: float,
    hidden_dim: int,
    dropout: float,
    threshold: float,
) -> tuple[list[dict[str, float]], int]:
    graphs = load_graph_data(str(dataset_dir))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = PackageGCN(hidden=hidden_dim, dropout=dropout).to(device)
    state = torch.load(model_path, map_location=device)
    model.load_state_dict(state)
    model.eval()

    per_seed: list[dict[str, float]] = []
    with torch.no_grad():
        for seed in seeds:
            _train, val = split_graphs_by_family(graphs, val_ratio=val_ratio, seed=seed)
            loader = GeometricDataLoader(val, batch_size=64)
            y_true: list[int] = []
            y_pred: list[int] = []
            for batch in loader:
                batch = batch.to(device)
                logits = model(batch.x, batch.edge_index, batch.batch)
                probs = torch.softmax(logits, dim=-1)[:, 1]
                preds = (probs >= threshold).long().detach().cpu().tolist()
                labels = batch.y.view(-1).detach().cpu().tolist()
                y_true.extend(labels)
                y_pred.extend(preds)
            per_seed.append(metrics_dict(y_true, y_pred))

    return per_seed, len(graphs)


def evaluate_isolation(model_dir: Path, dataset_csv: Path, seeds: list[int]) -> tuple[list[dict[str, float]], int]:
    model = joblib.load(model_dir / "model.joblib")
    scaler = joblib.load(model_dir / "scaler.joblib")
    metadata_path = model_dir / "metadata.joblib"
    metadata = joblib.load(metadata_path) if metadata_path.exists() else {"threshold": 0.0}
    threshold = float(metadata.get("threshold", 0.0))

    X: list[list[float]] = []
    y: list[int] = []
    with dataset_csv.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            X.append(
                [
                    float(row.get("account_age_days", 365)),
                    float(row.get("total_packages", 1)),
                    float(row.get("github_repos", 0)),
                    float(row.get("previous_downloads", 0)),
                    float(row.get("has_verified_email", 1)),
                ]
            )
            y.append(int(row.get("label", 0)))

    X_np = np.array(X, dtype=np.float32)
    y_np = np.array(y, dtype=np.int64)

    per_seed: list[dict[str, float]] = []
    for seed in seeds:
        rng = np.random.default_rng(seed)
        idx = rng.choice(len(X_np), size=len(X_np), replace=True)
        X_bs = X_np[idx]
        y_bs = y_np[idx]

        scores = model.decision_function(scaler.transform(X_bs))
        preds = (scores < threshold).astype(np.int64)
        per_seed.append(metrics_dict(y_bs.tolist(), preds.tolist()))

    return per_seed, len(X_np)


def main() -> None:
    parser = argparse.ArgumentParser(description="Realistic multi-seed evaluation with CI")
    parser.add_argument("--codebert_model", default="backend/ml_models/saved_models/codebert_best")
    parser.add_argument("--gnn_model", default="backend/ml_models/saved_models/gnn_best/model.pt")
    parser.add_argument("--isolation_model", default="backend/ml_models/saved_models/isolation_forest_best")
    parser.add_argument("--codebert_dataset", default="backend/ml_models/datasets/processed/codebert/dataset.csv")
    parser.add_argument("--gnn_dataset", default="backend/ml_models/datasets/processed/dependency_graphs")
    parser.add_argument("--isolation_dataset", default="backend/ml_models/datasets/processed/maintainers/maintainer_features.csv")
    parser.add_argument("--seeds", default="11,17,23,29,37")
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--gnn_hidden_dim", type=int, default=192)
    parser.add_argument("--gnn_dropout", type=float, default=0.45)
    parser.add_argument("--gnn_threshold", type=float, default=0.5)
    parser.add_argument("--out_json", default="backend/ml_models/saved_models/realistic_leaderboard.json")
    parser.add_argument("--out_md", default="backend/ml_models/saved_models/realistic_leaderboard.md")
    args = parser.parse_args()

    seeds = [int(x.strip()) for x in args.seeds.split(",") if x.strip()]

    cb_rows, cb_n = evaluate_codebert(Path(args.codebert_model), Path(args.codebert_dataset), seeds, args.val_ratio)
    gnn_rows, gnn_n = evaluate_gnn_thresholded(
        Path(args.gnn_model),
        Path(args.gnn_dataset),
        seeds,
        args.val_ratio,
        args.gnn_hidden_dim,
        args.gnn_dropout,
        args.gnn_threshold,
    )
    iso_rows, iso_n = evaluate_isolation(Path(args.isolation_model), Path(args.isolation_dataset), seeds)

    report = {
        "seeds": seeds,
        "codebert": {
            "sample_count": cb_n,
            "per_seed": cb_rows,
            "summary": summarize_with_ci(cb_rows),
            "protocol": "family-disjoint holdout, synthetic excluded",
        },
        "gnn": {
            "sample_count": gnn_n,
            "per_seed": gnn_rows,
            "summary": summarize_with_ci(gnn_rows),
            "protocol": f"family-disjoint holdout (threshold={args.gnn_threshold:.3f})",
        },
        "isolation_forest": {
            "sample_count": iso_n,
            "per_seed": iso_rows,
            "summary": summarize_with_ci(iso_rows),
            "protocol": "bootstrap evaluation using saved threshold",
        },
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    def fm(m: dict[str, float]) -> str:
        return f"{m['mean']:.4f} +/- {m['ci95']:.4f}"

    lines = [
        "# Realistic Leaderboard",
        "",
        f"Seeds: {seeds}",
        "",
        "| Model | Protocol | Accuracy (mean+/-CI95) | Precision (mean+/-CI95) | Recall (mean+/-CI95) | F1 (mean+/-CI95) |",
        "|---|---|---:|---:|---:|---:|",
        f"| CodeBERT | {report['codebert']['protocol']} | {fm(report['codebert']['summary']['accuracy'])} | {fm(report['codebert']['summary']['precision'])} | {fm(report['codebert']['summary']['recall'])} | {fm(report['codebert']['summary']['f1'])} |",
        f"| GNN | {report['gnn']['protocol']} | {fm(report['gnn']['summary']['accuracy'])} | {fm(report['gnn']['summary']['precision'])} | {fm(report['gnn']['summary']['recall'])} | {fm(report['gnn']['summary']['f1'])} |",
        f"| Isolation Forest | {report['isolation_forest']['protocol']} | {fm(report['isolation_forest']['summary']['accuracy'])} | {fm(report['isolation_forest']['summary']['precision'])} | {fm(report['isolation_forest']['summary']['recall'])} | {fm(report['isolation_forest']['summary']['f1'])} |",
    ]
    Path(args.out_md).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    print(f"Saved JSON report to {out_json}")
    print(f"Saved Markdown report to {args.out_md}")


if __name__ == "__main__":
    main()
