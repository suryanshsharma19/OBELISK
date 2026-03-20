#!/usr/bin/env python3
"""Fine-tune CodeBERT for malicious code classification."""

import argparse
import csv
import hashlib
import json
import random
import re
from pathlib import Path

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    get_linear_schedule_with_warmup,
)


class CodeDataset(Dataset):

    def __init__(self, samples: list[tuple[str, int, str]], tokenizer, max_len: int = 512):
        self.samples = samples
        self.tokenizer = tokenizer
        self.max_len = max_len

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        code, label, _family = self.samples[idx]
        encoding = self.tokenizer(
            code,
            truncation=True,
            max_length=self.max_len,
            padding="max_length",
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(0),
            "attention_mask": encoding["attention_mask"].squeeze(0),
            "label": torch.tensor(label, dtype=torch.long),
        }


def package_family(package: str) -> str:
    name = package.strip().lower()
    if name.startswith("synthetic-"):
        return name
    if "/" in name:
        name = name.split("/", 1)[0]
    token = re.split(r"[-_.]", name)[0]
    return token or "unknown"


def load_dataset(path: str, max_samples: int | None = None) -> list[tuple[str, int, str]]:
    samples: list[tuple[str, int, str]] = []
    seen: set[str] = set()
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            code = row["code"].strip()
            if len(code) < 40:
                continue
            label = int(row["label"])
            family = package_family(str(row.get("package", "unknown")))
            # Deduplicate exact code snippets to reduce memorization risk.
            digest = hashlib.sha1(code.encode("utf-8", errors="ignore")).hexdigest()
            if digest in seen:
                continue
            seen.add(digest)
            samples.append((code, label, family))
            if max_samples is not None and len(samples) >= max_samples:
                break

    # Fallback: use unified JSONL if CSV is sparse/malformed.
    if len(samples) < 100:
        dataset_path = Path(path)
        unified = dataset_path.parent.parent / "unified" / "unified_samples.jsonl"
        if unified.exists():
            print(f"CSV yielded {len(samples)} samples; falling back to {unified}")
            samples = []
            seen.clear()
            with unified.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if row.get("task") != "codebert":
                        continue
                    code = str(row.get("code", "")).strip()
                    if len(code) < 40:
                        continue
                    label = int(row.get("label", 0))
                    family = package_family(str(row.get("package", "unknown")))
                    digest = hashlib.sha1(code.encode("utf-8", errors="ignore")).hexdigest()
                    if digest in seen:
                        continue
                    seen.add(digest)
                    samples.append((code, label, family))
                    if max_samples is not None and len(samples) >= max_samples:
                        break

    print(f"Loaded {len(samples)} samples from {path}")
    return samples


def split_dataset(samples: list[tuple[str, int, str]], val_ratio: float, seed: int) -> tuple[list[tuple[str, int, str]], list[tuple[str, int, str]]]:
    rng = random.Random(seed)
    groups: dict[str, list[tuple[str, int, str]]] = {}
    for sample in samples:
        groups.setdefault(sample[2], []).append(sample)

    families = list(groups.keys())
    rng.shuffle(families)

    target_val = max(int(len(samples) * val_ratio), 1)
    train: list[tuple[str, int, str]] = []
    val: list[tuple[str, int, str]] = []
    val_count = 0
    for fam in families:
        items = groups[fam]
        if val_count < target_val:
            val.extend(items)
            val_count += len(items)
        else:
            train.extend(items)

    if not train or not val:
        shuffled = list(samples)
        rng.shuffle(shuffled)
        cut = max(int(len(shuffled) * (1.0 - val_ratio)), 1)
        train = shuffled[:cut]
        val = shuffled[cut:]

    return train, val


def evaluate(model, loader, device):
    model.eval()
    val_loss = 0.0
    tp = fp = fn = tn = 0
    with torch.no_grad():
        for batch in loader:
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            val_loss += outputs.loss.item()
            preds = torch.argmax(outputs.logits, dim=-1)

            tp += ((preds == 1) & (labels == 1)).sum().item()
            tn += ((preds == 0) & (labels == 0)).sum().item()
            fp += ((preds == 1) & (labels == 0)).sum().item()
            fn += ((preds == 0) & (labels == 1)).sum().item()

    total = tp + tn + fp + fn
    accuracy = (tp + tn) / max(total, 1)
    precision = tp / max(tp + fp, 1)
    recall = tp / max(tp + fn, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-8)

    return {
        "loss": val_loss / max(len(loader), 1),
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def train(args):
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    # Load pre-trained CodeBERT
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)
    model.config.hidden_dropout_prob = args.dropout
    model.config.attention_probs_dropout_prob = args.dropout
    model.to(device)

    # Prepare data
    samples = load_dataset(args.dataset, max_samples=args.max_samples)
    if len(samples) < args.min_unique_samples:
        raise RuntimeError(
            f"Insufficient unique samples ({len(samples)}). "
            f"Increase data diversity or lower --min_unique_samples."
        )
    train_samples, val_samples = split_dataset(samples, val_ratio=args.val_ratio, seed=args.seed)
    print(f"Train/Val split: {len(train_samples)} / {len(val_samples)}")

    train_ds = CodeDataset(train_samples, tokenizer, max_len=args.max_len)
    val_ds = CodeDataset(val_samples, tokenizer, max_len=args.max_len)

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        num_workers=args.num_workers,
        pin_memory=(device.type == "cuda"),
    )

    # Optimiser and scheduler
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)
    total_steps = max((len(train_loader) * args.epochs) // max(args.grad_accum_steps, 1), 1)
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=int(total_steps * args.warmup_ratio),
        num_training_steps=total_steps,
    )

    # Training loop
    best_f1 = -1.0
    stale_epochs = 0
    for epoch in range(1, args.epochs + 1):
        model.train()
        total_loss = 0.0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader, start=1):
            input_ids = batch["input_ids"].to(device)
            attention_mask = batch["attention_mask"].to(device)
            labels = batch["label"].to(device)

            outputs = model(input_ids=input_ids, attention_mask=attention_mask, labels=labels)
            loss = outputs.loss / max(args.grad_accum_steps, 1)

            loss.backward()
            if step % max(args.grad_accum_steps, 1) == 0 or step == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            total_loss += loss.item() * max(args.grad_accum_steps, 1)

        avg_train_loss = total_loss / max(len(train_loader), 1)
        metrics = evaluate(model, val_loader, device)

        print(
            f"Epoch {epoch}/{args.epochs} train_loss={avg_train_loss:.4f} "
            f"val_loss={metrics['loss']:.4f} val_acc={metrics['accuracy']*100:.1f}% "
            f"val_f1={metrics['f1']:.4f} precision={metrics['precision']:.4f} recall={metrics['recall']:.4f}"
        )

        # Save best model by validation F1 to encourage generalization.
        if metrics["f1"] > best_f1:
            best_f1 = metrics["f1"]
            stale_epochs = 0
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            model.save_pretrained(output_dir)
            tokenizer.save_pretrained(output_dir)
            print(f"  -> Saved best model to {output_dir}")
        else:
            stale_epochs += 1
            if stale_epochs >= args.early_stopping_patience:
                print("Early stopping triggered")
                break

    print(f"Training complete. Best val_f1={best_f1:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fine-tune CodeBERT")
    parser.add_argument("--dataset", required=True, help="Path to CSV dataset")
    parser.add_argument("--output", default="ml_models/saved_models/codebert", help="Output directory")
    parser.add_argument("--model_name", default="microsoft/codebert-base")
    parser.add_argument("--epochs", type=int, default=8)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--weight_decay", type=float, default=0.05)
    parser.add_argument("--warmup_ratio", type=float, default=0.1)
    parser.add_argument("--dropout", type=float, default=0.2)
    parser.add_argument("--max_len", type=int, default=256)
    parser.add_argument("--max_samples", type=int, default=200000)
    parser.add_argument("--val_ratio", type=float, default=0.15)
    parser.add_argument("--grad_accum_steps", type=int, default=2)
    parser.add_argument("--early_stopping_patience", type=int, default=3)
    parser.add_argument("--min_unique_samples", type=int, default=200)
    parser.add_argument("--num_workers", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    train(parser.parse_args())
