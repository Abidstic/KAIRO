# P2 — Structured Developer/Reviewer Profile Generation

**Paper reference:** Section 3 → **(P2)** structured expertise profile prompt (`lst:prompt-structured-profile` in the manuscript, if listed).

**Context (from the paper):** Section 3 → **(P2)** structured expertise profile prompt. A Python output parser turns unstructured skills analysis (from [P1](P1_skill_extraction_prompt.md)) into a structured developer/reviewer profile (six fields: name, experience level, primary skills, programming languages, summary, `javascript_skill_matrix`). In code this is one LangChain `PromptTemplate`: body below, `{format_instructions}`, then the closing REMEMBER block at the end of the prompt section.

**Model configuration:** `mistralai/ministral-8b-2512`, temperature 0.3, max tokens 4,000, served via OpenRouter.

**Template variables (developer):** `skills_analysis`, `developer_name`, `pr_count`, `repo_list`

**Injected partial variables:** `{valid_categories}` (17 category names), `{js_categories}` (from `js_skill_categories` in the notebook), `{format_instructions}` (Pydantic JSON schema instructions).

## Prompt (developer)

````
Based on the following JavaScript skills analysis, generate a comprehensive JavaScript developer profile:

Developer: {developer_name}
Total PRs: {pr_count}
Repositories: {repo_list}

Skills Analysis:
{skills_analysis}

VALID CATEGORY NAMES (THESE ARE THE ONLY ALLOWED KEYS):
{valid_categories}

JavaScript Skill Matrix Details:
{js_categories}

Generate a JavaScript developer profile that includes:
1. Experience level assessment (Junior/Mid/Senior/Lead) based on JavaScript contributions
2. Primary JavaScript technical skills and frameworks they show expertise in
3. Overall JavaScript developer summary
4. Detailed skill matrix mapping to the provided JavaScript categories WITH EMBEDDED FREQUENCY

========== CRITICAL RULES FOR javascript_skill_matrix ==========
YOU MUST FOLLOW THESE RULES EXACTLY OR THE OUTPUT WILL BE REJECTED:

FREQUENCY EMBEDDING RULES:
1. For each category that has skills, ADD the frequency count to the category name in the KEY
2. Format: "Category Name, frequency: X" where X is the total count for that category
3. For each individual skill, ALSO ADD the frequency count to the skill name in the VALUE
4. Format: "Skill Name, frequency: Y" where Y is the count for that specific skill
5. For categories with NO skills (empty arrays), DO NOT add frequency - just use the category name alone

CATEGORY NAME RULES:
1. ONLY use these EXACT base category names:
   - "Framework/Library Expertise"
   - "Asynchronous Programming"
   - "API Design & Consumption"
   - "Error Handling"
   - "Frontend Development Skills"
   - "Backend Development Skills"
   - "DevOps & Deployment"
   - "Advanced JavaScript Concepts"
   - "Functional Programming"
   - "Data Structures & Algorithms"
   - "TypeScript"
   - "Progressive Web Apps (PWA)"
   - "Mobile Development with JavaScript"
   - "Web Performance Optimization"
   - "Event-Driven Architecture"
   - "Dependency Management"
   - "Graphical Data Visualization"

2. DO NOT create any new category names
3. DO NOT use subcategory names like "Testing Libraries" or "Backend Frameworks"
4. DO NOT use individual skill names like "Node.js", "Express.js", "CI/CD" as category names
5. If you see skills related to testing (Jest, Mocha, etc.), count them under "Framework/Library Expertise"
6. If you see skills related to code quality, linting, etc., count them appropriately under existing categories

Example CORRECT javascript_skill_matrix:
{{
  "Framework/Library Expertise, frequency: 15": ["Node.js, frequency: 8", "Express.js, frequency: 5", "Jest, frequency: 2"],
  "Asynchronous Programming, frequency: 6": ["Promises, frequency: 4", "async/await, frequency: 2"],
  "API Design & Consumption, frequency: 10": ["RESTful APIs, frequency: 10"],
  "Backend Development Skills, frequency: 20": ["Middleware, frequency: 8", "API Endpoints, frequency: 7", "Authentication/Authorization, frequency: 5"],
  "DevOps & Deployment, frequency: 8": ["CI/CD Pipelines, frequency: 5", "Containerization, frequency: 3"],
  "Advanced JavaScript Concepts, frequency: 4": ["Prototypes & Inheritance, frequency: 2", "Module Systems, frequency: 2"],
  "Dependency Management, frequency: 12": ["npm/yarn, frequency: 12"],
  "Error Handling": [],
  "Frontend Development Skills": [],
  "Functional Programming": [],
  "Data Structures & Algorithms": [],
  "TypeScript": [],
  "Progressive Web Apps (PWA)": [],
  "Mobile Development with JavaScript": [],
  "Web Performance Optimization": [],
  "Event-Driven Architecture": [],
  "Graphical Data Visualization": []
}}

Example WRONG javascript_skill_matrix (DO NOT DO THIS):
{{
  "Testing Libraries, frequency: 5": ["Jest, frequency: 5"],  ← WRONG! "Testing Libraries" is not a main category
  "Node.js": ["Express.js"],  ← WRONG! "Node.js" is a skill, not a category
  "Framework/Library Expertise": ["Node.js", "Express.js"],  ← WRONG! Missing frequency for non-empty array AND individual skills
  "Framework/Library Expertise, frequency: 10": ["Node.js", "Express.js"]  ← WRONG! Missing frequency for individual skills
}}
========== END OF CRITICAL RULES FOR FREQUENCY EMBEDDING ==========

========== CRITICAL RULES FOR SKILL SELECTION ==========
YOU MUST FOLLOW THESE RULES EXACTLY FOR THE SKILL MATRIX:

1. The javascript_skill_matrix MUST use the EXACT 17 category names as keys
2. For each category, ONLY include skills that are EXPLICITLY LISTED in the subcategory definitions above
3. DO NOT add skills that are not in the predefined lists (e.g., "webpack", "babel", etc.)
4. If no evidence found for a category, use an empty array []
5. DO NOT invent or add new skills - ONLY use skills from the predefined lists

Example CORRECT javascript_skill_matrix:
{{
  "Framework/Library Expertise, frequency: 15": ["Node.js, frequency: 8", "Express.js, frequency: 5", "Jest, frequency: 2"],
  "API Design & Consumption, frequency: 10": ["RESTful APIs, frequency: 8", "Authentication & Authorization, frequency: 2"],
  "Backend Development Skills, frequency: 20": ["Middleware, frequency: 8", "API Endpoints, frequency: 12"],
  "Dependency Management, frequency: 12": ["npm/yarn, frequency: 12"],
  "TypeScript": []
}}

Example WRONG javascript_skill_matrix (DO NOT DO THIS):
{{
  "Framework/Library Expertise": ["Node.js", "Express.js", "webpack"],  ← WRONG! "webpack" not in list AND missing frequencies
  "API Design & Consumption, frequency: 10": ["RESTful APIs", "GraphQL", "custom-api"],  ← WRONG! "custom-api" not in list AND missing individual frequencies
  "DevOps & Deployment": ["CI/CD Pipelines", "Docker", "Kubernetes"]  ← WRONG! "Docker", "Kubernetes" not in list, AND missing frequencies
}}
========== END OF CRITICAL RULES ==========

========== CRITICAL RULES FOR JSON OUTPUT ==========
1. Return ONLY raw valid JSON — no markdown code fences (no ```json)
2. Do NOT include comments (no // or /* */)
3. Use \n for line breaks inside string values, not literal newlines
========== END JSON OUTPUT RULES ==========

{format_instructions}

Be specific and evidence-based in your JavaScript skill assessment. Map identified
skills to the appropriate categories, using evidence from PR titles, descriptions,
and file changes.

CATEGORY RULES:
- Only use the 17 exact predefined category names; DO NOT invent new categories or skills
- DO NOT use subcategory or individual skill names (e.g., "Testing Libraries", "Node.js") as category names
- Route testing skills (Jest, Mocha, etc.) under "Framework/Library Expertise"; route
  code-quality/linting skills under the existing category they best fit

FREQUENCY EMBEDDING RULES:
- For each non-empty category, embed the frequency count in BOTH the category name
  and each individual skill name
- Format: "Category Name, frequency: X": ["Skill Name, frequency: Y", ...]
- The category frequency is the SUM of its individual skill frequencies
- For categories with no skills, omit the frequency and use the category name alone

REMEMBER:
- Only use skills EXPLICITLY listed in the subcategory definitions for javascript_skill_matrix!
- DO NOT invent new skills or add skills not in the predefined lists!
````

**Note:** Doubled curly braces (`{{`, `}}`) in the examples match the Python template source; LangChain resolves them to single braces in the text sent to the model.

## Reviewer variant

Same rules and matrix structure as above.

**Template variables:** `skills_analysis`, `reviewer_name`, `review_count`, `repo_list`

Opening and checklist wording:

```
Based on the following JavaScript skills analysis, generate a comprehensive JavaScript reviewer profile:

Reviewer: {reviewer_name}
Total Reviews: {review_count}
Repositories: {repo_list}

...

VALID CATEGORY NAMES FOR skill_frequency (THESE ARE THE ONLY ALLOWED KEYS):
{valid_categories}

...

Generate a JavaScript reviewer profile that includes:
1. Experience level assessment (Junior/Mid/Senior/Lead) based on JavaScript review quality
2. Primary JavaScript technical skills and frameworks they show expertise in
3. Overall JavaScript reviewer summary
4. Detailed skill matrix mapping to the provided JavaScript categories WITH EMBEDDED FREQUENCY
```

The remainder of the template (critical rules, JSON output rules, `{format_instructions}`, category/frequency consistency rules, and REMEMBER block) matches the developer prompt, with reviewer-oriented skill-selection rule text where the notebook references `skill_frequency`.
