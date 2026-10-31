# P5 — LLM-Only Reviewer Matching (Ablation)

**Paper reference:** Section 4.4 (or ablation) → **“LLM Only”** configuration — manuscript prompt label **(P5)**.

**Approach (what the LLM receives):** Reviewer ranking uses the same PR requirement JSON ([P3](P3_pr_requirement_extraction_prompt.md)), FAISS-retrieved similar training PRs (`all-MiniLM-L6-v2`), and **plain-language reviewer profiles** from `newAnalysis/LLM/` — experience level, activity stats, `primary_skills`, LLM-inferred **`identified_skills`** categories, and **`skill_evidence`** snippets. There is **no** fixed KU skill matrix and **no** frequency-embedded category keys (unlike `LLM+KU+freq`).

**Implementation:** `newAnalysis/LLM/axios/PrecisionMetricsCalculation/TopThreeReviewerList.ipynb` → `SmartReviewerAssigner.matching_prompt`. Profiles are built with `newAnalysis/LLM/axios/Reviewer_profile.ipynb` (and matching `developer_profile.ipynb` for authors).

**Model configuration:** `mistralai/ministral-8b-2512`, temperature 0.1, max tokens 4,000, served via OpenRouter.

## Prompt

```
You are a deterministic reviewer ranking engine.

Task: rank the best 3 reviewers for this PR using the provided requirements, reviewer profiles, and similar past reviews.

Hard rules:
- Use only reviewers that appear in AVAILABLE REVIEWERS.
- Base every claim on the provided profile data or similar review evidence.
- Treat overlap between PR requirements and reviewer identified_skills / skill_evidence as the strongest signal of practical expertise.
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
- skill_match: 0.00 to 1.00, weight 0.45. Measures direct overlap between required skills/frameworks and reviewer identified_skills or skill_evidence.
- domain_alignment: 0.00 to 1.00, weight 0.20. Measures fit to the needed review type and expertise areas.
- similar_review_relevance: 0.00 to 1.00, weight 0.15. Measures match with retrieved similar PRs and review patterns.
- review_activity_consistency: 0.00 to 1.00, weight 0.10. Measures reviewer reliability from total reviews/comments/PRs reviewed.
- complexity_fit: 0.00 to 1.00, weight 0.10. Measures whether reviewer experience matches PR complexity.

Decision guidance:
- Rank by final weighted score, highest first.
- Use conservative scores when evidence is partial.
- If two reviewers are close, prefer the one with stronger skill overlap and more similar-review matches.
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
        "skill_match": 0.0,
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

**Note:** `{pr_requirements}`, `{reviewer_profiles}`, and `{similar_reviews}` are runtime placeholders. `{reviewer_profiles}` is a text summary per reviewer (identified skills, evidence, sample reviews). Doubled curly braces (`{{`, `}}`) escape literal braces in LangChain templates.
