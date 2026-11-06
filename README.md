# KAIRO — Replication Package

**A Hybrid LLM and Frequency-Weighted Knowledge Unit Approach for Pull Request Reviewer Recommendation**

This package contains everything needed to (1) reproduce the evaluation tables reported in the paper from the shipped outputs, (2) re-run the proposed LLM+KU+Frequency approach and its ablation variants, (3) re-run the four baseline algorithms (RevFinder, cHRev, TurnoverRec, Sofia), and (4) reproduce the failure analysis of unmatched recommendations.

> **All commands in this README are run from this `KAIRO/` folder unless stated otherwise.**

---

## Contents

1. [What the study does](#1-what-the-study-does)
2. [Repository layout](#2-repository-layout)
3. [Setup](#3-setup)
4. [Reproduce the paper's tables from the shipped outputs](#4-reproduce-the-papers-tables-from-the-shipped-outputs) (Tables 2–6)
5. [Re-run the proposed approach and the ablation study](#5-re-run-the-proposed-approach-and-the-ablation-study)
6. [Re-run the baseline models](#6-re-run-the-baseline-models)
7. [Rebuild the dataset from scratch](#7-rebuild-the-dataset-from-scratch)
8. [Paper-to-artifact map](#8-paper-to-artifact-map)

---

## 1. What the study does

We propose KAIRO, a hybrid approach that combines LLMs, frequency-weighted Knowledge Units (KUs), and semantic retrieval of historical PRs to recommend code reviewers. For each target PR the approach:

1. **Extracts technical requirements** from the PR using an LLM (prompt P3).
2. **Retrieves similar historical PRs** via FAISS embeddings (`all-MiniLM-L6-v2`).
3. **Ranks candidate reviewers** using structured developer and reviewer expertise profiles (17-category KU matrix with frequency counts) and an LLM (prompt P4).

The approach is evaluated across seven popular open-source JavaScript repositories and compared against four existing reviewer recommendation techniques. An ablation study examines the contributions of structured KUs and frequency weighting.

| Evidence | How it is used | Prompt |
|----------|---------------|--------|
| Developer/reviewer KU profiles with frequency | Expertise matching | P4 (full), P6 (binary KU), P5 (no KU) |
| Target PR requirements | Extracted from PR content and code changes | P3 |
| Similar historical PRs | Retrieved via FAISS cosine similarity | Included in P4/P5/P6 |

**Model configuration:** `mistralai/ministral-8b-2512` via OpenRouter, temperature 0.3 for profiling (P1, P2) and 0.1 for assignment (P3–P6).

## 2. Repository layout

```
KAIRO/
├── prompts/                     All LLM prompts (P1–P7) used in the pipeline
│   ├── P1  Skill extraction from PR activity
│   ├── P2  Structured profile generation (17-category KU matrix)
│   ├── P3  PR requirement extraction
│   ├── P4  Reviewer ranking — KU + frequency (full approach)
│   ├── P5  Reviewer ranking — LLM-only ablation
│   ├── P6  Reviewer ranking — KU binary ablation
│   └── P7  Failure analysis explanation
│
├── data-collection/             GitHub crawler for collecting repository PR/commit data
│
├── proposed-approach/           KAIRO pipeline
│   ├── scripts/                   PR data fetching and train/test splitting
│   └── notebooks/                 Profile generation, reviewer assignment, evaluation
│       ├── developer_profile.ipynb          Generate developer profiles (P1 → P2)
│       ├── Reviewer_profile.ipynb           Generate reviewer profiles (P1 → P2)
│       ├── TopThreeReviewerList.ipynb       Bulk reviewer assignment (P3 → FAISS → P4/P5/P6)
│       ├── SinglePRAssignment_Reviewer.ipynb Single PR assignment demo
│       ├── Actual_PR_Reviewer_Extractor.ipynb Extract ground-truth assignments
│       └── Reviewer_Metrics_Evaluation.ipynb  Compute evaluation metrics
│
├── baseline-models/             Baseline algorithms: RevFinder, cHRev, TurnoverRec, Sofia
│   └── src/                       Algorithm implementations and evaluation
│
├── results/                     All evaluation results (shipped outputs)
│   ├── proposed-LLM+KU+Freq/     Full approach (7 repos)
│   ├── ablation-LLM-only/        Ablation: LLM-only, no KU (9 repos)
│   ├── ablation-LLM+KU/          Ablation: KU binary, no frequency (9 repos)
│   └── baseline-models/           RevFinder, cHRev, TurnoverRec, Sofia (7 repos)
│
└── failure-analysis/            Analysis of unmatched recommendations (RQ2)
    ├── unified-data/              Per-repo records for each mismatched PR
    └── results/                   Aggregated failure analysis evaluation
```

### Per-repository result structure

Each repository folder under `results/proposed-LLM+KU+Freq/`, `results/ablation-LLM-only/`, and `results/ablation-LLM+KU/` contains:

```
{repo}/
├── developer-profiles/    Generated developer skill profiles (JSON)
├── reviewer-profiles/     Generated reviewer skill profiles (JSON)
└── evaluation/
    ├── actual_pr_reviewer_assignments.json      Ground-truth reviewer assignments
    ├── all_pr_reviewer_assignments.json          Model predictions (top 3 per PR)
    ├── pr_reviewer_evaluation_metrics.json       Aggregate evaluation metrics
    └── reviewer_miss_failure_analysis.json       Per-PR failure analysis (proposed only)
```

## 3. Setup

| Needed for | Requirement |
|------------|-------------|
| Everything | Python 3.9+, `pip install -r requirements.txt` (in each subfolder) |
| Proposed approach (§5) | Jupyter Notebook or JupyterLab, OpenRouter API key |
| Baseline models (§6) | GitHub personal access token (for data crawling) |
| Data collection (§7) | GitHub personal access token |

```bash
# Proposed approach
cd proposed-approach
pip install -r requirements.txt

# Baseline models
cd ../baseline-models
pip install -r requirements.txt
```

For the LLM pipeline, set your API credentials:

```bash
export OPENROUTER_API_KEY="your_openrouter_key"
```

Or set them inside the notebooks:

```python
import os
os.environ["OPENROUTER_API_KEY"] = "your_key_here"
os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
```

---

## 4. Reproduce the paper's tables from the shipped outputs

This section maps every table in the paper to the shipped output files in `results/` and `failure-analysis/`. No LLM calls or data collection are needed — the evaluation results are pre-computed and shipped.

### Table 1 — Repository characteristics and PR distribution

**Paper reference:** Section 3.2, Table 1.

Table 1 reports the characteristics (stars, commits, contributors, PRs opened) and the developer/reviewer PR distribution (profiling and evaluation splits) for each of the seven subject repositories. These statistics were collected at the time of data collection (October 31, 2025) and are reported directly in the paper.

| Repository | Stars | Commits | Contributors | PRs Opened | Dev PRs (Profile / Eval.) | Reviewer PRs (Profile / Eval.) |
|-----------|-------|---------|-------------|-----------|--------------------------|-------------------------------|
| Express.js | 68,853 | 6,091 | 366 | 2,191 | 500 (400 / 100) | 152 (131 / 21) |
| jQuery | 59,581 | 6,791 | 365 | 3,095 | 500 (400 / 100) | 390 (308 / 82) |
| Moment.js | 47,836 | 4,064 | 680 | 2,083 | 500 (400 / 100) | 108 (79 / 29) |
| Lodash | 61,064 | 7,676 | 262 | 1,459 | 500 (400 / 100) | 97 (77 / 20) |
| Axios | 108,640 | 1,756 | 534 | 1,996 | 500 (400 / 100) | 154 (117 / 37) |
| Chart.js | 67,345 | 4,580 | 524 | 3,885 | 500 (400 / 100) | 429 (350 / 79) |
| Preact | 38,660 | 6,067 | 367 | 2,699 | 500 (400 / 100) | 442 (344 / 98) |

### Table 2 — Proposed approach performance (RQ1)

**Paper reference:** Section 4.1, Table 2.

Table 2 reports Hit@3, MAP@3, and MRR for the full LLM+KU+Frequency approach. The paper evaluates on the **reviewer evaluation subset** (the "Reviewer PRs Eval." column of Table 1) — only PRs with recorded reviewers.

**Source files:** `results/proposed-LLM+KU+Freq/{repo}/evaluation/`

- `all_pr_reviewer_assignments.json` — the model's top-3 predictions per PR
- `actual_pr_reviewer_assignments.json` — ground-truth reviewer assignments
- `pr_reviewer_evaluation_metrics.json` — pre-computed aggregate metrics

**To verify:** Open `proposed-approach/notebooks/Reviewer_Metrics_Evaluation.ipynb`, point it at the evaluation files for each repository, and run all cells. The notebook computes Hit@3, MAP@3, MRR, and additional metrics.

**Expected results (from the paper):**

| Repository | Hit@3 (%) | MAP@3 (%) | MRR (%) |
|-----------|----------|----------|--------|
| Express.js | 76.19 | 53.33 | 58.73 |
| jQuery | 96.34 | 71.75 | 75.41 |
| Lodash | 0.00 | 0.00 | 0.00 |
| Moment.js | 3.45 | 1.15 | 3.45 |
| Chart.js | 100.00 | 68.74 | 80.17 |
| Preact | 82.65 | 50.79 | 59.52 |
| Axios | 54.05 | 41.76 | 46.40 |
| **Average** | **58.95** | **41.07** | **46.24** |

### Table 3 — Case study: KU profile comparison (RQ2)

**Paper reference:** Section 4.2, Table 3.

Table 3 compares the KU profiles of the actual reviewer and the top-ranked recommended reviewer for Express.js PR #6754 as an illustrative case. This data is extracted from:

- `results/proposed-LLM+KU+Freq/express/reviewer-profiles/` — reviewer profiles with KU frequencies
- `results/proposed-LLM+KU+Freq/express/evaluation/all_pr_reviewer_assignments.json` — the model's recommendation for PR #6754

### Table 4 — Suitability analysis of unmatched recommendations (RQ2)

**Paper reference:** Section 4.2, Table 4.

Table 4 reports the justification rates for unmatched recommendations across the seven repositories. The analysis covers 81 PRs where none of the top-3 recommended reviewers matched the actual reviewers.

**Source file:** `failure-analysis/results/failure_eval_results.json`

This file contains the overall and per-repository counts of analyzed PRs, justified top-1 and top-3 recommendations, and their percentages.

**Expected results (from the paper):**

| Repository | Analyzed PRs | Top-1 Justified (%) | Top-3 Justified (%) |
|-----------|-------------|---------------------|---------------------|
| Express.js | 5 | 4 (80.0) | 4 (80.0) |
| Axios | 12 | 7 (58.3) | 9 (75.0) |
| Lodash | 19 | 13 (68.4) | 15 (78.9) |
| Moment.js | 28 | 23 (82.1) | 25 (89.3) |
| Preact | 17 | 10 (58.8) | 11 (64.7) |
| jQuery | 0 | -- | -- |
| Chart.js | 0 | -- | -- |
| **Overall** | **81** | **57 (70.4)** | **64 (79.0)** |

**Supporting data:** `failure-analysis/unified-data/unified_{repo}.json` — per-PR records containing PR metadata, requirements, actual reviewer profiles, and suggested reviewer profiles used in the analysis.

### Table 5 — Comparison with baseline techniques (RQ3)

**Paper reference:** Section 4.3, Table 5.

Table 5 compares our approach against RevFinder, cHRev, TurnoverRec, and Sofia.

**Source files:**

- `results/proposed-LLM+KU+Freq/{repo}/evaluation/pr_reviewer_evaluation_metrics.json` — proposed approach metrics
- `results/baseline-models/{owner}-{repo}_target_eval_{timestamp}.json` — baseline metrics per repository

Each baseline result file contains a `metrics` object with keys `RevFinder`, `ChRev`, `TurnoverRec`, and `Sofia`, each holding `precision@3`, `hit@3`, `map@3`, and `mrr`.

**To verify baselines:** See [§6](#6-re-run-the-baseline-models) for how to re-run the baseline algorithms.

**Expected results (from the paper):**

| Repository | LLM+KU+Freq Hit@3 | RevFinder Hit@3 | cHRev Hit@3 | TurnoverRec Hit@3 | Sofia Hit@3 |
|-----------|-------------------|----------------|------------|------------------|------------|
| Express.js | 76.2 | 50.0 | 20.0 | 0.0 | 20.0 |
| jQuery | 96.3 | 100.0 | 73.2 | 11.0 | 53.7 |
| Lodash | 0.0 | 5.0 | 0.0 | 5.0 | 5.0 |
| Moment.js | 3.5 | 18.5 | 7.4 | 0.0 | 7.4 |
| Chart.js | 100.0 | 96.2 | 70.9 | 12.7 | 70.9 |
| Preact | 82.7 | 79.6 | 60.2 | 10.2 | 58.2 |
| Axios | 54.1 | 96.6 | 62.1 | 20.7 | 62.1 |
| **Average** | **59.0** | **63.7** | **42.0** | **8.5** | **39.6** |

See the paper for the full table including MAP@3 and MRR for all approaches.

### Table 6 — Ablation study (RQ4)

**Paper reference:** Section 4.4, Table 6.

Table 6 compares three configurations: LLM Only, LLM+KU (Binary), and LLM+KU+Frequency.

**Source files:**

| Configuration | Results folder | Matching prompt |
|--------------|---------------|----------------|
| LLM Only | `results/ablation-LLM-only/` | P5 |
| LLM + KU (Binary) | `results/ablation-LLM+KU/` | P6 |
| LLM + KU + Frequency (full) | `results/proposed-LLM+KU+Freq/` | P4 |

Each folder contains per-repository evaluation metrics in `{repo}/evaluation/pr_reviewer_evaluation_metrics.json`.

**Expected results (from the paper):**

| Repository | LLM Only Hit@3 | LLM+KU Hit@3 | LLM+KU+Freq Hit@3 |
|-----------|----------------|--------------|-------------------|
| Express.js | 57.1 | 66.7 | 76.2 |
| jQuery | 96.3 | 93.9 | 96.3 |
| Lodash | 0.0 | 0.0 | 0.0 |
| Moment.js | 0.0 | 3.5 | 3.5 |
| Chart.js | 97.5 | 97.5 | 100.0 |
| Preact | 58.2 | 83.7 | 82.7 |
| Axios | 54.1 | 64.9 | 54.1 |
| **Average** | **51.9** | **58.6** | **59.0** |

See the paper for the full table including MAP@3 and MRR for all configurations.

### Figure 3 — Cross-repository comparison heatmap

**Paper reference:** Section 4.3, Figure 3.

The heatmap visualizes the results of Table 5. The data source is the same as Table 5 above.

---

## 5. Re-run the proposed approach and the ablation study

Full details: [`proposed-approach/README.md`](proposed-approach/README.md).

### Step 1 — Collect PR data

Configure the repository details and API token in `proposed-approach/scripts/DeveloperFetchData.py` and `proposed-approach/scripts/ReviewerFetchData.py`, then run:

```bash
cd proposed-approach/scripts
python DeveloperFetchData.py
python ReviewerFetchData.py
```

### Step 2 — Create train/test split

```bash
python split_pr_data.py {path/to/all_pr_data.json} 0.9
```

Sorts PRs chronologically by `created_at` and splits 80/20 (profiling / evaluation).

### Step 3 — Generate expertise profiles

Open and run the following notebooks in `proposed-approach/notebooks/`:

1. `developer_profile.ipynb` — generates developer profiles using P1 (skill extraction) and P2 (structured profile)
2. `Reviewer_profile.ipynb` — generates reviewer profiles using P1 and P2

Both use `mistralai/ministral-8b-2512` at temperature 0.3 with checkpointing for long runs.

### Step 4 — Generate reviewer predictions

Open `proposed-approach/notebooks/TopThreeReviewerList.ipynb`. This notebook:

1. Extracts requirements from each evaluation PR using P3
2. Retrieves similar historical PRs via FAISS embeddings
3. Ranks top 3 reviewers using the matching prompt (P4, P5, or P6 depending on the variant)

| Variant | Profile format | Matching prompt |
|---------|---------------|----------------|
| **LLM Only** | Free-form `identified_skills` | P5 |
| **LLM + KU (Binary)** | 17-category KU matrix (binary) | P6 |
| **LLM + KU + Frequency** (full) | KU matrix with frequency counts | P4 |

### Step 5 — Evaluate predictions

1. Run `Actual_PR_Reviewer_Extractor.ipynb` to extract ground-truth reviewer assignments
2. Run `Reviewer_Metrics_Evaluation.ipynb` to compute Hit@3, MAP@3, MRR, and additional metrics

Results are saved to JSON in the evaluation output directory.

---

## 6. Re-run the baseline models

Full details: [`baseline-models/README.md`](baseline-models/README.md).

### Step 1 — Crawl repository data

```bash
cd data-collection
python3 main.py --owner expressjs --repo express
```

Repeat for all seven repositories: `jquery/jquery`, `lodash/lodash`, `moment/moment`, `axios/axios`, `chartjs/Chart.js`, `preactjs/preact`.

### Step 2 — Set the data directory

```bash
export DATA_BASE_DIR=/path/to/data-collection/crawled-data
```

### Step 3 — Run the baseline algorithms

```bash
cd baseline-models/src
python3 manager.py --r_owner expressjs --r_name express algo-revFinder
python3 manager.py --r_owner expressjs --r_name express algo-chRev
python3 manager.py --r_owner expressjs --r_name express algo-turnoverRec
python3 manager.py --r_owner expressjs --r_name express algo-sofia
```

Repeat for all seven repositories.

### Step 4 — Evaluate

```bash
python3 manager.py evaluate --r_owner expressjs --r_name express
```

Pre-computed baseline results for all repositories are shipped in `results/baseline-models/`.

---

## 7. Rebuild the dataset from scratch

The shipped results in `results/` are the exact outputs evaluated in the paper. To rebuild from scratch:

1. **Crawl PR data** using `data-collection/` (requires a GitHub token)
2. **Fetch developer and reviewer PR data** using `proposed-approach/scripts/`
3. **Follow the pipeline** in [§5](#5-re-run-the-proposed-approach-and-the-ablation-study)

Detailed instructions are in [`data-collection/README.md`](data-collection/README.md) and [`proposed-approach/README.md`](proposed-approach/README.md).

**Note on exact reproducibility.** Mining queries the live GitHub API, so a re-run may return a slightly different dataset (PRs deleted, repositories archived, review data updated). The shipped `results/` folder is the exact snapshot evaluated in the paper.

---

## 8. Paper-to-artifact map

| Paper section | Artifact |
|--------------|---------|
| §3.1 — KU construction | The 17 KUs are described in the paper; used in prompts P2, P4, P6 |
| §3.2 — Repository and PR selection | `data-collection/`, `proposed-approach/scripts/` |
| §3.3 — Profile construction (P1, P2) | `proposed-approach/notebooks/developer_profile.ipynb`, `Reviewer_profile.ipynb` |
| §3.3 — Historical PR index | FAISS index built in `TopThreeReviewerList.ipynb` |
| §3.4 — PR requirement extraction (P3) | `prompts/P3_pr_requirement_extraction_prompt.md`, `TopThreeReviewerList.ipynb` |
| §3.4 — Reviewer ranking (P4) | `prompts/P4_reviewer_matching_prompt.md`, `TopThreeReviewerList.ipynb` |
| Table 1 — Repository characteristics | Statistics collected at data-collection time (October 31, 2025) |
| Table 2 — Proposed approach (RQ1) | `results/proposed-LLM+KU+Freq/` |
| Table 3 — Case study KU comparison | `results/proposed-LLM+KU+Freq/express/reviewer-profiles/` |
| Table 4 — Unmatched recommendations (RQ2) | `failure-analysis/results/failure_eval_results.json`, `failure-analysis/unified-data/` |
| Table 5 — Baseline comparison (RQ3) | `results/baseline-models/`, `results/proposed-LLM+KU+Freq/` |
| Table 6 — Ablation study (RQ4) | `results/ablation-LLM-only/`, `results/ablation-LLM+KU/`, `results/proposed-LLM+KU+Freq/` |
| Figure 2 — Profile construction | `proposed-approach/notebooks/developer_profile.ipynb`, `Reviewer_profile.ipynb` |
| Figure 3 — Cross-repository heatmap | Derived from Table 5 data |
| Figure 4 — Recommendation pipeline | `proposed-approach/notebooks/TopThreeReviewerList.ipynb` |
| All prompts (P1–P7) | `prompts/` |

## Subject Repositories

| Repository | Proposed approach | Ablation variants | Baseline models | Failure analysis |
|-----------|:-:|:-:|:-:|:-:|
| Express.js | x | x | x | x |
| jQuery | x | x | x | x |
| Lodash | x | x | x | x |
| Moment.js | x | x | x | x |
| Axios | x | x | x | x |
| Chart.js | x | x | x | |
| Preact | x | x | x | x |
| Fastify | | x | | |
| npm CLI | | x | | |

## Model Settings

| Stage | Model | Temperature |
|-------|-------|-------------|
| P1, P2 (profiles) | `mistralai/ministral-8b-2512` via OpenRouter | 0.3 |
| P3–P6 (assignment) | `mistralai/ministral-8b-2512` via OpenRouter | 0.1 |

## License

See [LICENSE](LICENSE).
