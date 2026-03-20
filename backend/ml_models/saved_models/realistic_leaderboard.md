# Realistic Leaderboard

Seeds: [11, 17, 23, 29, 37]

| Model | Protocol | Accuracy (mean+/-CI95) | Precision (mean+/-CI95) | Recall (mean+/-CI95) | F1 (mean+/-CI95) |
|---|---|---:|---:|---:|---:|
| CodeBERT | family-disjoint holdout, synthetic excluded | 0.8471 +/- 0.0072 | 0.8362 +/- 0.0135 | 0.8707 +/- 0.0291 | 0.8528 +/- 0.0159 |
| GNN | family-disjoint holdout (threshold=0.500) | 0.6435 +/- 0.0507 | 0.6435 +/- 0.0507 | 1.0000 +/- 0.0000 | 0.7819 +/- 0.0370 |
| Isolation Forest | bootstrap evaluation using saved threshold | 0.5507 +/- 0.0181 | 0.7375 +/- 0.0149 | 0.5069 +/- 0.0185 | 0.6007 +/- 0.0165 |
