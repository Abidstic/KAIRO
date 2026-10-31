# KAIRO (Knowledge-unit AI Reviewer recommendation)

Replication package for the KAIRO paper: an LLM-based pull request reviewer recommendation system that builds developer and reviewer profiles using knowledge units (KU) and frequency information, then ranks candidate reviewers for incoming PRs.

## Repository Structure

| Folder | What it contains |
|--------|-----------------|
| [`prompts/`](prompts/) | All LLM prompts (P1–P7) used in the pipeline |
| [`data-collection/`](data-collection/) | GitHub crawler for collecting repository PR/commit data |
| [`proposed-approach/`](proposed-approach/) | KAIRO pipeline: scripts and notebooks for profile generation, reviewer assignment, and evaluation |
| [`baseline-models/`](baseline-models/) | Baseline algorithms (RevFinder, cHRev, TurnoverRec, Sofia) for comparison |
| [`results/`](results/) | All evaluation results: proposed approach, ablation variants, baselines, and failure analysis |
| [`failure-analysis/`](failure-analysis/) | Unified per-repo data and evaluation for mismatched predictions |

## Pipeline Overview

```
GitHub PR history
       │
       ▼
[P1] Skill extraction from PR activity
       │
       ▼
[P2] Structured developer/reviewer profiles (17-category KU matrix)
       │
       ▼
[P3] PR requirement extraction (per target PR)
       │
       ▼
     FAISS similar-PR retrieval
       │
       ▼
[P4] Reviewer ranking (top 3) using KU + frequency
       │
       ▼
     Evaluation: Precision, Recall, F1, MRR, NDCG, Hit Rate
```

## Ablation Study

Three configurations tested across all subject repositories:

| Variant | Profile format | Matching prompt | Results folder |
|---------|---------------|----------------|----------------|
| **LLM-only** | Free-form `identified_skills` | P5 | `results/ablation-LLM-only/` |
| **LLM+KU** | 17-category KU matrix (binary) | P6 | `results/ablation-LLM+KU/` |
| **LLM+KU+Freq** (full) | KU matrix with frequency counts | P4 | `results/proposed-LLM+KU+Freq/` |

## Subject Repositories

| Repository | Proposed approach | Ablation variants | Failure analysis |
|-----------|:-:|:-:|:-:|
| Express | x | x | x |
| jQuery | x | x | x |
| Lodash | x | x | x |
| Moment | x | x | x |
| Axios | x | x | x |
| Chart.js | x | x | |
| Preact | x | x | x |
| Fastify | | x | |
| npm CLI | | x | |

## Quick Start

### Reproduce the proposed approach

```bash
cd proposed-approach
pip install -r requirements.txt
```

Then follow the step-by-step instructions in [`proposed-approach/README.md`](proposed-approach/README.md).

### Run baseline models

```bash
cd baseline-models
pip install -r requirements.txt
```

See [`baseline-models/README.md`](baseline-models/README.md) for setup and execution.

### Verify published results

All evaluation metric JSONs are in [`results/`](results/). See [`results/README.md`](results/README.md) for the mapping between result files and paper tables.

## Model Settings

| Stage | Model | Temperature |
|-------|-------|-------------|
| P1, P2 (profiles) | `mistralai/ministral-8b-2512` via OpenRouter | 0.3 |
| P3–P6 (assignment) | `mistralai/ministral-8b-2512` via OpenRouter | 0.1 |

## Requirements

- Python 3.9+
- Jupyter Notebook or JupyterLab
- GitHub personal access token (for data collection)
- OpenRouter API key (for LLM-based profile generation and assignment)

## License

See [LICENSE](LICENSE).
