# Data Collection — GitHub Crawler

A GitHub repository crawler that extracts pull requests, commits, reviews, files, and comments for use in the KAIRO pipeline and baseline model evaluation.

## Setup

```bash
pip install -r requirements.txt
export GH_TOKEN='your_github_personal_access_token'
```

Or run the interactive setup:

```bash
python3 setup.py
```

## Usage

### Crawl a repository

```bash
python3 main.py --owner expressjs --repo express
```

### Limit the crawl scope

```bash
python3 main.py --owner jquery --repo jquery --limit 100 --selection latest
```

### Validate crawled data quality

```bash
python3 data_quality_analyzer.py crawled-data/expressjs-express
```

## Output Structure

```
crawled-data/{owner}-{repo}/
├── pull/
│   ├── all_data.json
│   └── {pr_number}/
│       ├── files/all_data.json
│       ├── reviews/all_data.json
│       ├── comments/all_data.json
│       └── commits/all_data.json
├── commit/
│   ├── all_data.json
│   └── all/{commit_sha}.json
└── logs/
```

## Features

- Automatic rate limit management
- Checkpoint/resume on interruption
- Parallel processing
- Data quality scoring for reviewer recommendation suitability

## Role in the Pipeline

The crawled data serves two purposes:

1. **Baseline models** — the crawled-data directory is read directly by RevFinder, cHRev, TurnoverRec, and Sofia (see `baseline-models/`).
2. **Proposed approach** — the scripts in `proposed-approach/scripts/` (`DeveloperFetchData.py`, `ReviewerFetchData.py`) collect and normalize PR data for the LLM pipeline. These scripts call the GitHub API directly and do not depend on this crawler.
