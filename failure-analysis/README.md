# Failure Analysis

Analysis of cases where the KAIRO system's suggested reviewer(s) did not match the actual reviewer.

## Contents

### `unified-data/`

Per-repository JSON files containing unified records for each mismatched PR. Each record includes:
- PR metadata and requirements
- Actual reviewer profile
- Suggested reviewer profiles (top 3)

Files: `axios.json`, `express.json`, `jquery.json`, `lodash.json`, `moment.json`, `preact.json`

### `results/`

- `failure_eval_results.json` — aggregated failure analysis evaluation across all repositories

## Methodology

For each PR where the predicted top-3 reviewers did not include the actual reviewer:
1. The actual reviewer's profile was compared against the suggested reviewers' profiles
2. The PR requirements were matched against each profile's knowledge units
3. Prompt **P7** was used for LLM-assisted failure explanation

## Repositories Covered

Express, jQuery, Lodash, Moment, Axios, Preact (6 of the 7 proposed-approach repositories; Chart.js excluded).
