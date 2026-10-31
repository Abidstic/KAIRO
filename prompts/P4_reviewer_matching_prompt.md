# P4 — Reviewer Matching and Ranking (LLM + KU + freq)

**Paper reference:** Section 3 (Method) → "Construct LLM Prompt" / reviewer recommendation — manuscript **(P4)** / **Listing 7** (`lst:prompt-reviewer-matching`).

**Context (from the paper):** Persona-based prompt (no few-shot, chain-of-thought, or self-consistency). Combines structured PR requirements ([P3](P3_pr_requirement_extraction_prompt.md)), reviewer profiles with **frequency-embedded** `javascript_skill_matrix` / KU evidence ([P2](P2_structured_profile_prompt.md)), and similar historical PRs from the FAISS index (`sentence-transformers/all-MiniLM-L6-v2`). Ablations: [P5](P5_llm_only_reviewer_matching_prompt.md) (no KU), [P6](P6_llm_ku_binary_reviewer_matching_prompt.md) (KU binary, no frequency).

**Implementation:** `newAnalysis/LLM+KU+freq/axios/PrecisionMetricsCalculation/TopThreeReviewerList.ipynb` → `SmartReviewerAssigner.matching_prompt`.

**Model configuration:** `mistralai/ministral-8b-2512`, temperature 0.1, max tokens 4,000, served via OpenRouter.

## Prompt

```
You are a deterministic reviewer ranking engine.

Task: rank the best 3 reviewers for this PR using the provided requirements, reviewer profiles, and similar past reviews.

Hard rules:
- Use only reviewers that appear in AVAILABLE REVIEWERS.
- Base every claim on the provided profile data or similar review evidence.
- Treat frequency counts as the strongest signal of practical expertise.
- Prefer direct matches over general seniority.
- Penalize reviewers with weak or missing evidence for the required skills.
- Return JSON only. No markdown, no explanation, no code fences.

PR REQUIREMENTS:
{pr_requirements}

AVAILABLE REVIEWERS:
{reviewer_profiles}

SIMILAR PAST REVIEWS:
{similar_reviews}

Scoring rubric:
- skill_frequency_match: 0.00 to 1.00, weight 0.45. Measures direct overlap between required skills/frameworks and reviewer frequency evidence.
- domain_alignment: 0.00 to 1.00, weight 0.20. Measures fit to the needed review type and expertise areas.
- similar_review_relevance: 0.00 to 1.00, weight 0.15. Measures match with retrieved similar PRs and review patterns.
- review_activity_consistency: 0.00 to 1.00, weight 0.10. Measures reviewer reliability from total reviews/comments/PRs reviewed.
- complexity_fit: 0.00 to 1.00, weight 0.10. Measures whether reviewer experience matches PR complexity.

Decision guidance:
- Rank by final weighted score, highest first.
- Use conservative scores when evidence is partial.
- If two reviewers are close, prefer the one with stronger frequency evidence and more similar-review matches.
- Make the reasoning short, factual, and specific.
- Provide exactly 3 reviewers.

Return exactly this JSON shape:
{{
  "recommended_reviewers": [
    {{
      "reviewer_name": "name",
      "match_score": 0.0,
      "reasoning": "short evidence-based explanation",
      "strengths_alignment": ["specific strength 1", "specific strength 2"],
      "review_experience": "short factual summary",
      "potential_concerns": "specific gap or None identified",
      "score_breakdown": {{
        "skill_frequency_match": 0.0,
        "domain_alignment": 0.0,
        "similar_review_relevance": 0.0,
        "review_activity_consistency": 0.0,
        "complexity_fit": 0.0
      }},
      "evidence": ["evidence 1", "evidence 2"]
    }}
  ],
  "assignment_confidence": "High|Medium|Low",
  "assignment_reasoning": "one short sentence explaining the top choice",
  "ranking_notes": ["note 1", "note 2"]
}}

Validation rules:
1. match_score and all score_breakdown values must be between 0 and 1.
2. The list must be sorted by match_score descending.
3. strengths_alignment and evidence must contain only concrete evidence phrases.
4. If the data is weak, lower the scores rather than inflating confidence.

JSON:
```

**Note:** `{pr_requirements}`, `{reviewer_profiles}`, and `{similar_reviews}` are runtime placeholders. Doubled curly braces (`{{`, `}}`) escape literal braces in LangChain templates.
