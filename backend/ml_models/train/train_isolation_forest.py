#!/usr/bin/env python3
"""
Train an Isolation Forest for maintainer anomaly detection.

Fits an unsupervised Isolation Forest on numeric features derived from
maintainer profiles (account age, package count, download history, etc.).

Dataset format (CSV):
    account_age_days,total_packages,github_repos,previous_downloads,has_verified_email
    365,12,5,150000,1
    2,1,0,0,0

Usage:
    python train_isolation_forest.py --dataset ../datasets/maintainers.csv \\
                                     --output  ../saved_models/isolation_forest
"""

import argparse
from pathlib import Path

import numpy as np


def load_data(path: str) -> np.ndarray:
    """Load the CSV and return a numpy array of features."""
    import csv
    rows = []
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
    data = np.array(rows, dtype=np.float32)
    print(f"Loaded {data.shape[0]} samples with {data.shape[1]} features")
    return data


def train(args):
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    import joblib

    data = load_data(args.dataset)

    # Standardise features for better isolation
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(data)

    # Fit Isolation Forest
    model = IsolationForest(
        n_estimators=args.n_estimators,
        contamination=args.contamination,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_scaled)

    # Score the training set to see the distribution
    scores = model.decision_function(X_scaled)
    predictions = model.predict(X_scaled)
    n_anomalies = (predictions == -1).sum()

    print(f"Anomalies detected in training data: {n_anomalies}/{len(data)}")
    print(f"Score range: [{scores.min():.4f}, {scores.max():.4f}]")

    # Save model + scaler
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, output / "model.joblib")
    joblib.dump(scaler, output / "scaler.joblib")
    print(f"Model saved to {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Isolation Forest")
    parser.add_argument("--dataset", required=True, help="Path to maintainer CSV")
    parser.add_argument("--output", default="ml_models/saved_models/isolation_forest")
    parser.add_argument("--n_estimators", type=int, default=200)
    parser.add_argument("--contamination", type=float, default=0.1)
    train(parser.parse_args())
