#!/usr/bin/env python3
"""Train an Isolation Forest for maintainer anomaly detection."""

import argparse
from pathlib import Path

import numpy as np


def load_data(path: str) -> tuple[np.ndarray, np.ndarray]:
    import csv
    rows = []
    labels = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            features = [
                float(row.get("account_age_days", 365)),
                float(row.get("total_packages", 1)),
                float(row.get("github_repos", 0)),
                float(row.get("previous_downloads", 0)),
                float(row.get("has_verified_email", 1)),
            ]
            rows.append(features)
            label = row.get("label")
            labels.append(int(label) if label is not None and str(label).strip() != "" else 0)
    data = np.array(rows, dtype=np.float32)
    y = np.array(labels, dtype=np.int64)
    print(f"Loaded {data.shape[0]} samples with {data.shape[1]} features")
    return data, y


def train(args):
    from sklearn.ensemble import IsolationForest
    from sklearn.metrics import f1_score, precision_score, recall_score
    from sklearn.preprocessing import StandardScaler
    import joblib

    data, real_labels = load_data(args.dataset)

    rng = np.random.default_rng(args.seed)
    labels = real_labels.copy() if args.use_dataset_labels else np.zeros(len(data), dtype=np.int64)
    if args.synthetic_anomaly_ratio > 0:
        # Add synthetic outliers for threshold calibration when labels are unavailable.
        n_syn = max(int(len(data) * args.synthetic_anomaly_ratio), 1)
        syn = rng.normal(
            loc=np.mean(data, axis=0) + np.std(data, axis=0) * args.synthetic_shift,
            scale=np.std(data, axis=0) * 1.5,
            size=(n_syn, data.shape[1]),
        ).astype(np.float32)
        data = np.vstack([data, syn])
        labels = np.concatenate([labels, np.ones(n_syn, dtype=np.int64)])

    idx = np.arange(len(data))
    rng.shuffle(idx)
    data = data[idx]
    labels = labels[idx]

    split_idx = int(len(data) * (1.0 - args.val_ratio))
    X_train = data[:split_idx]
    y_train = labels[:split_idx]
    X_val = data[split_idx:]
    y_val = labels[split_idx:]

    benign_train = X_train[y_train == 0]
    if len(benign_train) == 0:
        raise RuntimeError("No benign samples available for Isolation Forest training")

    # Standardise features for better isolation
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(benign_train)
    X_val_scaled = scaler.transform(X_val) if len(X_val) else np.empty((0, data.shape[1]))

    # Fit Isolation Forest
    model = IsolationForest(
        n_estimators=args.n_estimators,
        contamination=args.contamination,
        random_state=42,
        n_jobs=-1,
        max_samples=args.max_samples,
        max_features=args.max_features,
        bootstrap=args.bootstrap,
    )
    model.fit(X_train_scaled)

    # Score validation data and calibrate anomaly threshold.
    if len(X_val_scaled):
        val_scores = model.decision_function(X_val_scaled)

        best = {
            "f1": -1.0,
            "precision": 0.0,
            "recall": 0.0,
            "threshold": 0.0,
            "quantile": args.threshold_quantile,
        }
        quantiles = np.linspace(args.threshold_sweep_min, args.threshold_sweep_max, args.threshold_sweep_steps)
        for q in quantiles:
            threshold = np.quantile(val_scores, q)
            val_preds = (val_scores < threshold).astype(int)
            precision = precision_score(y_val, val_preds, zero_division=0)
            recall = recall_score(y_val, val_preds, zero_division=0)
            f1 = f1_score(y_val, val_preds, zero_division=0)

            if f1 > best["f1"] or (f1 == best["f1"] and recall > best["recall"]):
                best = {
                    "f1": float(f1),
                    "precision": float(precision),
                    "recall": float(recall),
                    "threshold": float(threshold),
                    "quantile": float(q),
                }

        threshold = best["threshold"]
        print(
            f"Validation precision={best['precision']:.4f} recall={best['recall']:.4f} "
            f"f1={best['f1']:.4f} threshold={threshold:.5f} quantile={best['quantile']:.3f}"
        )
    else:
        threshold = 0.0
        best = {
            "f1": 0.0,
            "precision": 0.0,
            "recall": 0.0,
            "threshold": 0.0,
            "quantile": 0.0,
        }
        print("Validation split empty; threshold set to 0.0")

    # Inspect full score distribution for sanity.
    full_scores = model.decision_function(scaler.transform(data))
    print(f"Score range: [{full_scores.min():.4f}, {full_scores.max():.4f}]")

    # Save model + scaler
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output / "model.joblib")
    joblib.dump(scaler, output / "scaler.joblib")
    joblib.dump(
        {
            "threshold": float(threshold),
            "validation": best,
            "feature_names": [
                "account_age_days",
                "total_packages",
                "github_repos",
                "previous_downloads",
                "has_verified_email",
            ],
        },
        output / "metadata.joblib",
    )
    print(f"Model saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Isolation Forest")
    parser.add_argument("--dataset", required=True, help="Path to maintainer CSV")
    parser.add_argument("--output", default="ml_models/saved_models/isolation_forest")
    parser.add_argument("--n_estimators", type=int, default=500)
    parser.add_argument("--contamination", type=float, default=0.05)
    parser.add_argument("--max_samples", default="auto")
    parser.add_argument("--max_features", type=float, default=1.0)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--threshold_quantile", type=float, default=0.08)
    parser.add_argument("--threshold_sweep_min", type=float, default=0.02)
    parser.add_argument("--threshold_sweep_max", type=float, default=0.25)
    parser.add_argument("--threshold_sweep_steps", type=int, default=25)
    parser.add_argument("--synthetic_anomaly_ratio", type=float, default=0.1)
    parser.add_argument("--synthetic_shift", type=float, default=3.0)
    parser.add_argument("--use_dataset_labels", action="store_true", help="Use label column from dataset for calibration")
    parser.add_argument("--seed", type=int, default=42)
    train(parser.parse_args())
