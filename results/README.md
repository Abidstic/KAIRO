# Results

All evaluation results organized by experiment variant.

## Folder Structure

```
results/
├── proposed-LLM+KU+Freq/     Full KAIRO approach (7 repos)
├── ablation-LLM-only/         Ablation: LLM-only, no KU (9 repos)
├── ablation-LLM+KU/           Ablation: KU binary, no frequency (9 repos)
└── baseline-models/            RevFinder, cHRev, TurnoverRec, Sofia
```

## Per-Repository Contents

Each repository folder contains:

```
{repo}/
├── developer-profiles/    Generated developer skill profiles (JSON)
├── reviewer-profiles/     Generated reviewer skill profiles (JSON)
└── evaluation/
    ├── actual_pr_reviewer_assignments.json
    ├── all_pr_reviewer_assignments.json
    └── pr_reviewer_evaluation_metrics.json
```

- `actual_pr_reviewer_assignments.json` — ground-truth reviewer assignments extracted from review data
- `all_pr_reviewer_assignments.json` — model predictions (top 3 ranked reviewers per PR)
- `pr_reviewer_evaluation_metrics.json` — aggregate evaluation metrics (precision, recall, F1, MRR, NDCG, hit rate, etc.)

## Baseline Results

The `baseline-models/` folder contains pre-computed evaluation results from running RevFinder, cHRev, TurnoverRec, and Sofia on the same repositories. See [`baseline-models/README.md`](../baseline-models/README.md) for how to reproduce.
