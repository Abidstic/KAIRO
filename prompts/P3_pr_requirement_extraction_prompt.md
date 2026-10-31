# P4 — PR Requirement Field Extraction

**Paper reference:** Section 3 (Method) → "Analyze Target PR" — manuscript **(P3)** / **Listing 5** (`lst:prompt-pr-analysis`).

**Context (from the paper):** When a new PR is submitted, the pipeline converts it to a text summary and analyzes it with an LLM to extract technical skill requirements, expertise domains, complexity level, and review focus areas. The model must identify only requirements supported by the PR content and code changes, avoiding unsupported assumptions. Results are combined with FAISS-retrieved similar PRs and structured profiles for reviewer recommendation ([P6](P6_reviewer_matching_prompt.md)).

**Model configuration:** `mistralai/ministral-8b-2512`, temperature 0.1, max tokens 4,000, served via OpenRouter.

**Implementation:** `TopThreeReviewerList.ipynb` → `SmartReviewerAssigner.analysis_prompt`. The string sent to the model is **this prompt block immediately followed by** [P5](P5_json_output_format_prompt.md) with no text omitted.

## Prompt (field extraction — Listing 5)

```
You are a strict PR requirement extraction engine for reviewer assignment.

Goal: infer the minimum set of reviewer requirements from the PR content and code changes. Be precise, conservative, and evidence-based.

Rules:
- Use only facts supported by the provided PR content and code changes.
- Do not mention technologies, frameworks, or domains unless there is clear evidence.
- Prefer fewer, higher-confidence requirements over broad guesses.
- If something is not explicit, omit it or use an empty array.
- Return JSON only. No markdown, no explanation, no code fences.

PR CONTENT:
{pr_content}

CODE CHANGES:
{code_changes}

Extract these fields:
- technical_skills_needed: concrete technologies, libraries, languages, or APIs required to review this PR
- review_expertise_areas_needed: review domains such as backend, testing, security, performance, docs, release, architecture
- complexity_level: Low, Medium, or High based on scope, risk, and implementation depth
- review_focus_areas: the exact aspects a reviewer should inspect
- primary_language: the main implementation language, or Unknown if not clear
- frameworks_involved: only frameworks/libraries clearly present in the PR
- review_type_needed: the single best review type from Code Quality, Security, Performance, Documentation, Architecture, or Testing

Scoring mindset for extraction:
- Prefer explicit names and exact terms from the PR.
- Treat version bumps, dependency changes, and config-only changes as high-signal only when the changed package or config is identifiable.
- If the PR is a dependency upgrade, include the upgraded package name and the ecosystem it belongs to.
- If the PR is documentation-only, keep technical skills minimal and set review_type_needed to Documentation.
- If the PR is test-only, prioritize Testing and the runtime language/framework involved.
```

## Full analysis prompt (P4 + P5, matches notebook)

```
You are a strict PR requirement extraction engine for reviewer assignment.

Goal: infer the minimum set of reviewer requirements from the PR content and code changes. Be precise, conservative, and evidence-based.

Rules:
- Use only facts supported by the provided PR content and code changes.
- Do not mention technologies, frameworks, or domains unless there is clear evidence.
- Prefer fewer, higher-confidence requirements over broad guesses.
- If something is not explicit, omit it or use an empty array.
- Return JSON only. No markdown, no explanation, no code fences.

PR CONTENT:
{pr_content}

CODE CHANGES:
{code_changes}

Extract these fields:
- technical_skills_needed: concrete technologies, libraries, languages, or APIs required to review this PR
- review_expertise_areas_needed: review domains such as backend, testing, security, performance, docs, release, architecture
- complexity_level: Low, Medium, or High based on scope, risk, and implementation depth
- review_focus_areas: the exact aspects a reviewer should inspect
- primary_language: the main implementation language, or Unknown if not clear
- frameworks_involved: only frameworks/libraries clearly present in the PR
- review_type_needed: the single best review type from Code Quality, Security, Performance, Documentation, Architecture, or Testing

Scoring mindset for extraction:
- Prefer explicit names and exact terms from the PR.
- Treat version bumps, dependency changes, and config-only changes as high-signal only when the changed package or config is identifiable.
- If the PR is a dependency upgrade, include the upgraded package name and the ecosystem it belongs to.
- If the PR is documentation-only, keep technical skills minimal and set review_type_needed to Documentation.
- If the PR is test-only, prioritize Testing and the runtime language/framework involved.

Return exactly this JSON shape:
{{
  "technical_skills_needed": ["skill1", "skill2"],
  "review_expertise_areas_needed": ["area1", "area2"],
  "complexity_level": "Low|Medium|High",
  "review_focus_areas": ["focus1", "focus2"],
  "primary_language": "language-or-Unknown",
  "frameworks_involved": ["framework1", "framework2"],
  "review_type_needed": "Code Quality|Security|Performance|Documentation|Architecture|Testing"
}}

Before responding, verify:
1. Every array item is supported by evidence in the input.
2. No field contains prose, bullets, or markdown.
3. The output is valid JSON with double-quoted keys and string values.
4. If evidence is weak, reduce the number of returned items rather than inventing them.

JSON:
```

**Note:** `{pr_content}` and `{code_changes}` are LangChain template placeholders. Doubled curly braces (`{{`, `}}`) in the JSON example match the notebook escape for literal braces.
