# LLM Prompts

These Markdown files are the canonical text of every LLM prompt used in the KAIRO pipeline.

## Prompt Map

| File | Label | Purpose | Used by |
|------|-------|---------|---------|
| [P1](P1_skill_extraction.md) | P1 | Extract JavaScript skills from a developer's PR history (narrative) | Profile notebooks |
| [P2](P2_structured_profile.md) | P2 | Convert narrative into a structured 17-category KU skill matrix | Profile notebooks |
| [P3](P3_pr_requirement_extraction.md) | P3 | Analyze a target PR and extract requirements as JSON | `TopThreeReviewerList.ipynb` (all variants) |
| [P4](P4_reviewer_matching_ku_freq.md) | P4 | Rank top 3 reviewers — **KU + frequency** (full approach) | `LLM+KU+Freq` variant |
| [P5](P5_llm_only_reviewer_matching.md) | P5 | Rank top 3 reviewers — **LLM-only** ablation (no KU, no frequency) | `LLM-only` variant |
| [P6](P6_ku_binary_reviewer_matching.md) | P6 | Rank top 3 reviewers — **KU binary** ablation (no frequency) | `LLM+KU` variant |
| [P7](P7_failure_analysis.md) | P7 | Explain missed predictions during failure analysis | Failure analysis |

## Which notebook uses which prompt?

All three ablation variants share the same **P3** PR-analysis prompt. Only the matching prompt and profile format differ:

| Experiment variant | Matching prompt |
|-------------------|----------------|
| `LLM-only` | P5 |
| `LLM+KU` | P6 |
| `LLM+KU+Freq` (full) | P4 |

## End-to-End Flow

```
P1 → P2  (build profiles offline)
       ↓
P3       (extract requirements from target PR)
       ↓
FAISS    (retrieve similar historical PRs)
       ↓
P4/P5/P6 (rank top 3 reviewers, depending on variant)
```
