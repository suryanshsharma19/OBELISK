#!/usr/bin/env python3
"""
Train a Graph Neural Network for dependency-graph classification.

Uses PyTorch Geometric to build a simple GCN that predicts whether a
package subgraph is malicious.

Dataset:
    A directory of JSON files, each describing a dependency graph:
      { "root": "pkg-name", "nodes": [...], "edges": [...], "label": 0|1 }

Usage:
    python train_gnn.py --dataset ../datasets/graphs/ \\
                        --output  ../saved_models/gnn \\
                        --epochs  50
"""

import argparse
import json
from pathlib import Path

import torch
import torch.nn.functional as F
from torch_geometric.data import Data, DataLoader
from torch_geometric.nn import GCNConv, global_mean_pool


# ---------------------------------------------------------------
# Model definition
# ---------------------------------------------------------------

class PackageGCN(torch.nn.Module):
    """Two-layer GCN with global mean pooling for graph classification."""

    def __init__(self, in_channels: int = 4, hidden: int = 64, out_channels: int = 2):
        super().__init__()
        self.conv1 = GCNConv(in_channels, hidden)
        self.conv2 = GCNConv(hidden, hidden)
        self.classifier = torch.nn.Linear(hidden, out_channels)

    def forward(self, x, edge_index, batch):
        x = self.conv1(x, edge_index)
        x = F.relu(x)
        x = F.dropout(x, p=0.3, training=self.training)
        x = self.conv2(x, edge_index)
        x = F.relu(x)
        x = global_mean_pool(x, batch)
        return self.classifier(x)


# ---------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------

def load_graph_data(dataset_dir: str) -> list[Data]:
    """Read JSON graph files and convert to PyG Data objects."""
    data_list = []
    dataset_path = Path(dataset_dir)

    for file in sorted(dataset_path.glob("*.json")):
        with open(file) as f:
            graph = json.load(f)

        num_nodes = len(graph.get("nodes", []))
        if num_nodes == 0:
            continue

        # Node features: [risk_score_norm, is_malicious, download_count_log, dep_count]
        x = torch.zeros(num_nodes, 4)
        for i, node in enumerate(graph["nodes"]):
            x[i][0] = node.get("risk_score", 0) / 100.0
            x[i][1] = float(node.get("is_malicious", False))
            x[i][2] = min(node.get("downloads", 0) / 1e6, 1.0)
            x[i][3] = min(node.get("dep_count", 0) / 50.0, 1.0)

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

        data_list.append(Data(x=x, edge_index=edge_index, y=torch.tensor([label])))

    print(f"Loaded {len(data_list)} graphs from {dataset_dir}")
    return data_list


# ---------------------------------------------------------------
# Training
# ---------------------------------------------------------------

def train(args):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    graphs = load_graph_data(args.dataset)
    if not graphs:
        print("No graph data found. Exiting.")
        return

    split = int(len(graphs) * 0.8)
    train_loader = DataLoader(graphs[:split], batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(graphs[split:], batch_size=args.batch_size)

    model = PackageGCN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = torch.nn.CrossEntropyLoss()

    best_acc = 0.0
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
        correct = 0
        total = 0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(device)
                out = model(batch.x, batch.edge_index, batch.batch)
                preds = out.argmax(dim=-1)
                correct += (preds == batch.y.view(-1)).sum().item()
                total += batch.y.size(0)

        acc = correct / max(total, 1) * 100
        print(f"Epoch {epoch:3d}  loss={total_loss / max(len(train_loader), 1):.4f}  val_acc={acc:.1f}%")

        if acc > best_acc:
            best_acc = acc
            output = Path(args.output)
            output.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output / "model.pt")
            print(f"  → Saved (acc={acc:.1f}%)")

    print(f"Training complete. Best accuracy: {best_acc:.1f}%")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train GNN for graph classification")
    parser.add_argument("--dataset", required=True, help="Directory of JSON graphs")
    parser.add_argument("--output", default="ml_models/saved_models/gnn")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    train(parser.parse_args())
