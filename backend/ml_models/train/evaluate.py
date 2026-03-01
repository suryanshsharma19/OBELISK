#!/usr/bin/env python3
"""Model evaluation - run saved models against a test dataset."""

import argparse
import csv
import json
from pathlib import Path

import numpy as np


def evaluate_codebert(model_path: str, dataset_path: str) -> dict:
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()

    # Load test data
    samples = []
    with open(dataset_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            samples.append((row["code"], int(row["label"])))

    predictions = []
    labels = []

    with torch.no_grad():
        for code, label in samples:
            inputs = tokenizer(code, return_tensors="pt", truncation=True, max_length=512, padding=True)
            outputs = model(**inputs)
            pred = torch.argmax(outputs.logits, dim=-1).item()
            predictions.append(pred)
            labels.append(label)

    return _compute_metrics(labels, predictions)


def evaluate_isolation_forest(model_path: str, dataset_path: str) -> dict:
    import joblib

    model = joblib.load(Path(model_path) / "model.joblib")
    scaler = joblib.load(Path(model_path) / "scaler.joblib")

    data = []
    labels = []
    with open(dataset_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            features = [
                float(row.get("account_age_days", 365)),
                float(row.get("total_packages", 1)),
                float(row.get("github_repos", 0)),
                float(row.get("previous_downloads", 0)),
                float(row.get("has_verified_email", 1)),
            ]
            data.append(features)
            # Label: 1 = anomalous (malicious), 0 = normal
            labels.append(int(row.get("label", 0)))

    X = np.array(data, dtype=np.float32)
    X_scaled = scaler.transform(X)

    # Isolation Forest: -1 = anomaly, 1 = normal
    raw_preds = model.predict(X_scaled)
    predictions = [1 if p == -1 else 0 for p in raw_preds]

    return _compute_metrics(labels, predictions)


def _compute_metrics(labels: list[int], predictions: list[int]) -> dict:
    tp = sum(1 for l, p in zip(labels, predictions) if l == 1 and p == 1)
    fp = sum(1 for l, p in zip(labels, predictions) if l == 0 and p == 1)
    fn = sum(1 for l, p in zip(labels, predictions) if l == 1 and p == 0)
    tn = sum(1 for l, p in zip(labels, predictions) if l == 0 and p == 0)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / max(len(labels), 1)

    metrics = {
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1, 4),
        "confusion_matrix": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "total_samples": len(labels),
    }
    return metrics


def main(args):
    print(f"Evaluating model: {args.model}")
    print(f"Dataset: {args.dataset}")

    if args.model == "codebert":
        model_path = args.model_path or "ml_models/saved_models/codebert"
        metrics = evaluate_codebert(model_path, args.dataset)
    elif args.model == "isolation_forest":
        model_path = args.model_path or "ml_models/saved_models/isolation_forest"
        metrics = evaluate_isolation_forest(model_path, args.dataset)
    else:
        print(f"Unknown model type: {args.model}")
        return

    print("\n--- Evaluation Results ---")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate trained models")
    parser.add_argument("--model", required=True, choices=["codebert", "isolation_forest", "gnn"])
    parser.add_argument("--dataset", required=True, help="Path to test dataset")
    parser.add_argument("--model_path", help="Override model directory")
    main(parser.parse_args())
