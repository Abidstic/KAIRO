# Proposed Approach — KAIRO Pipeline

End-to-end instructions for running the KAIRO reviewer recommendation pipeline.

## Prerequisites

```bash
pip install -r requirements.txt
```

Required packages: `jupyter`, `requests`, `pandas`, `numpy`, `pydantic`, `langchain`, `langchain-openai`, `sentence-transformers`, `faiss-cpu`.

Set your API credentials:

```python
import os
os.environ["OPENROUTER_API_KEY"] = "your_key_here"
os.environ["OPENAI_API_KEY"] = os.environ["OPENROUTER_API_KEY"]
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
```

## Step 1: Collect PR Data

Configure repository details in `scripts/DeveloperFetchData.py` and `scripts/ReviewerFetchData.py`, then run:

```bash
cd scripts
python DeveloperFetchData.py
python ReviewerFetchData.py
```

This produces developer-oriented and reviewer-oriented PR JSON files.

## Step 2: Create Train/Test Split

```bash
python split_pr_data.py path/to/all_pr_data.json 0.9
```

The script sorts PRs by `created_at` and splits chronologically (default 90/10 for the full approach).

## Step 3: Generate Profiles

Open `notebooks/developer_profile.ipynb` and `notebooks/Reviewer_profile.ipynb`. Set the input paths and API configuration, then run all cells.

- Uses **P1** (skill extraction) and **P2** (structured profile) prompts
- Model: `mistralai/ministral-8b-2512` at temperature 0.3
- Includes checkpointing for long runs

## Step 4: Generate Reviewer Predictions

Open `notebooks/TopThreeReviewerList.ipynb`. This notebook:

1. Extracts requirements from each test PR using **P3**
2. Retrieves similar historical PRs via FAISS embeddings
3. Ranks top 3 reviewers using **P4** (or P5/P6 for ablation)

For a single PR, use `notebooks/SinglePRAssignment_Reviewer.ipynb`.

## Step 5: Evaluate Predictions

1. Run `notebooks/Actual_PR_Reviewer_Extractor.ipynb` to extract ground-truth assignments
2. Run `notebooks/Reviewer_Metrics_Evaluation.ipynb` to compute metrics

Metrics computed: top-k accuracy, precision, recall, F1, hit rate, MRR, MAP, DCG/NDCG, and stability measures.

## Ablation Variants

To run an ablation variant, change only the matching prompt and profile format:

| Variant | Profile format | Matching prompt |
|---------|---------------|----------------|
| LLM-only | Free-form skills | P5 |
| LLM+KU | Binary KU matrix | P6 |
| LLM+KU+Freq (full) | KU matrix + frequency | P4 |

## Notebooks

| Notebook | Purpose |
|----------|---------|
| `developer_profile.ipynb` | Generate developer profiles from PR activity |
| `Reviewer_profile.ipynb` | Generate reviewer profiles from review activity |
| `SinglePRAssignment_Developer.ipynb` | Recommend a developer for a single PR |
| `SinglePRAssignment_Reviewer.ipynb` | Recommend a reviewer for a single PR |
| `TopThreeReviewerList.ipynb` | Bulk reviewer assignment (top 3 predictions) |
| `Actual_PR_Reviewer_Extractor.ipynb` | Extract actual reviewer assignments from data |
| `Reviewer_Metrics_Evaluation.ipynb` | Compute evaluation metrics |
