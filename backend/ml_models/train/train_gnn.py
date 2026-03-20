#!/usr/bin/env python3
"""Train a GNN for dependency-graph classification."""

import argparse
import json
import random
import re
import copy
from pathlib import Path

import torch
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.loader import DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool


class PackageGCN(torch.nn.Module):

    def __init__(self, in_channels: int = 2, hidden: int = 128, out_channels: int = 2, dropout: float = 0.35):
        super().__init__()
        self.dropout = dropout
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.conv3 = GCNConv(hidden, hidden)
        self.classifier = torch.nn.Linear(hidden, out_channels)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv3(x, edge_index)
        x = F.relu(x)
        x = global_mean_pool(x, batch)
        return self.classifier(x)


def load_graph_data(dataset_dir: str) -> list[Data]:
    data_list = []
    dataset_path = Path(dataset_dir)

    for file in sorted(dataset_path.glob("*.json")):
        with open(file) as f:
            graph = json.load(f)

        num_nodes = len(graph.get("nodes", []))
        if num_nodes == 0:
            continue

        # Node features: [download_count_norm, dep_count_norm]
        # Intentionally excludes risk_score/is_malicious because they encode labels.
        x = torch.zeros(num_nodes, 2)
        for i, node in enumerate(graph["nodes"]):
            x[i][0] = min(node.get("downloads", 0) / 1e6, 1.0)
            x[i][1] = min(node.get("dep_count", 0) / 50.0, 1.0)

        # Edges
        edges = graph.get("edges", [])
        if edges:
            edge_index = torch.tensor(
                [[e[0] for e in edges], [e[1] for e in edges]],
                dtype=torch.long,
            )
        else:
            edge_index = torch.zeros(2, 0, dtype=torch.long)

        label = int(graph.get("label", 0))
        package = str(graph.get("package", "unknown"))
        data = Data(x=x, edge_index=edge_index, y=torch.tensor([label]))
        data.package = package
        data.family = graph_family_key(package)
        data_list.append(data)

    print(f"Loaded {len(data_list)} graphs from {dataset_dir}")
    return data_list


def graph_family_key(package: str) -> str:
    name = package.strip().lower()
    if "/" in name:
        name = name.split("/", 1)[0]
    token = re.split(r"[-_.]", name)[0]
    return token or "unknown"


def split_graphs_by_family(graphs: list[Data], val_ratio: float, seed: int) -> tuple[list[Data], list[Data]]:
    grouped: dict[str, list[Data]] = {}
    for g in graphs:
        grouped.setdefault(getattr(g, "family", "unknown"), []).append(g)

    groups = list(grouped.items())
    rng = random.Random(seed)
    rng.shuffle(groups)

    target_val = max(int(len(graphs) * val_ratio), 1)
    train: list[Data] = []
    val: list[Data] = []
    val_count = 0
    for _, items in groups:
        if val_count < target_val:
            val.extend(items)
            val_count += len(items)
        else:
            train.extend(items)

    if not train or not val:
        # Fallback to random split if family groups are too coarse.
        shuffled = list(graphs)
        rng.shuffle(shuffled)
        cut = max(int(len(shuffled) * (1.0 - val_ratio)), 1)
        train = shuffled[:cut]
        val = shuffled[cut:]
    return train, val


def build_hard_negatives(train_graphs: list[Data], ratio: float, seed: int) -> list[Data]:
    if ratio <= 0:
        return []

    benign = [g for g in train_graphs if int(g.y.item()) == 0]
    if not benign:
        return []

    rng = random.Random(seed)
    target = int(len(train_graphs) * ratio)
    hard_negatives: list[Data] = []

    for _ in range(target):
        source = rng.choice(benign)
        g = copy.deepcopy(source)

        # Make benign samples harder: increase feature overlap with risky profiles
        # while preserving benign label to discourage false positives.
        x = g.x.clone()
        noise0 = torch.randn_like(x[:, 0]) * 0.05
        noise1 = torch.randn_like(x[:, 1]) * 0.06
        x[:, 0] = torch.clamp(x[:, 0] * rng.uniform(0.9, 1.5) + noise0, 0.0, 1.0)
        x[:, 1] = torch.clamp(x[:, 1] * rng.uniform(1.1, 1.9) + noise1, 0.0, 1.0)
        g.x = x
        g.y = torch.tensor([0], dtype=torch.long)
        hard_negatives.append(g)

    return hard_negatives


def train(args):
    random.seed(args.seed)
    torch.manual_seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    graphs = load_graph_data(args.dataset)
    if not graphs:
        print("No graph data found. Exiting.")
        return

    train_graphs, val_graphs = split_graphs_by_family(graphs, val_ratio=args.val_ratio, seed=args.seed)
    hard_negatives = build_hard_negatives(train_graphs, ratio=args.hard_negative_ratio, seed=args.seed)
    if hard_negatives:
        train_graphs = train_graphs + hard_negatives
        print(f"Added hard negatives: {len(hard_negatives)}")
    print(f"Train/Val split: {len(train_graphs)} / {len(val_graphs)} (family-disjoint)")

    train_loader = DataLoader(train_graphs, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_graphs, batch_size=args.batch_size)

    model = PackageGCN(hidden=args.hidden_dim, dropout=args.dropout).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=args.weight_decay)

    train_labels = [int(g.y.item()) for g in train_graphs]
    pos = sum(1 for y in train_labels if y == 1)
    neg = sum(1 for y in train_labels if y == 0)
    # class balancing to reduce overfitting to majority class
    w0 = len(train_labels) / max(2 * neg, 1)
    w1 = len(train_labels) / max(2 * pos, 1)
    w0 *= args.negative_weight_boost
    class_weights = torch.tensor([w0, w1], dtype=torch.float32, device=device)
    criterion = torch.nn.CrossEntropyLoss(weight=class_weights)

    best_f1 = -1.0
    stale_epochs = 0
    for epoch in range(1, args.epochs + 1):
        # Train
        model.train()
        total_loss = 0
        for batch in train_loader:
            batch = batch.to(device)
            optimizer.zero_grad()
            out = model(batch.x, batch.edge_index, batch.batch)
            loss = criterion(out, batch.y.view(-1))
            loss.backward()
            optimizer.step()
            total_loss += loss.item()

        # Validate
        model.eval()
        tp = fp = fn = tn = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.batch)
                preds = out.argmax(dim=-1)
                labels = batch.y.view(-1)
                tp += ((preds == 1) & (labels == 1)).sum().item()
                tn += ((preds == 0) & (labels == 0)).sum().item()
                fp += ((preds == 1) & (labels == 0)).sum().item()
                fn += ((preds == 0) & (labels == 1)).sum().item()

        total = tp + tn + fp + fn
        acc = (tp + tn) / max(total, 1)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)

        print(
            f"Epoch {epoch:3d} loss={total_loss / max(len(train_loader), 1):.4f} "
            f"val_acc={acc*100:.1f}% val_f1={f1:.4f} precision={precision:.4f} recall={recall:.4f}"
        )

        if f1 > best_f1:
            best_f1 = f1
            stale_epochs = 0
            output = Path(args.output)
            output.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output / "model.pt")
            print(f"  -> Saved (val_f1={f1:.4f})")
        else:
            stale_epochs += 1
            if stale_epochs >= args.early_stopping_patience:
                print("Early stopping triggered")
                break

    print(f"Training complete. Best val_f1: {best_f1:.4f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train GNN for graph classification")
    parser.add_argument("--dataset", required=True, help="Directory of JSON graphs")
    parser.add_argument("--output", default="ml_models/saved_models/gnn")
    parser.add_argument("--epochs", type=int, default=120)
    parser.add_argument("--batch_size", type=int, default=64)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--weight_decay", type=float, default=1e-4)
    parser.add_argument("--dropout", type=float, default=0.35)
    parser.add_argument("--hidden_dim", type=int, default=128)
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--negative_weight_boost", type=float, default=1.0)
    parser.add_argument("--hard_negative_ratio", type=float, default=0.0)
    parser.add_argument("--early_stopping_patience", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    train(parser.parse_args())
