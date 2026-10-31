import json
import os
import time
import uuid

import requests

API_TOKEN = os.environ.get("GH_TOKEN", "")

REPO_OWNER = "fastify"
REPO_NAME = "fastify"
OUTPUT_SUBDIR = "fastify"
base_repo_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls"
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}


def github_get(url, params=None, max_retries=5):
    """GET with retry on rate limits and transient errors."""
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers, params=params, timeout=60)

        if response.status_code == 200:
            return response

        if response.status_code in (403, 429):
            retry_after = int(response.headers.get("Retry-After", 60))
            print(f"Rate limited (status {response.status_code}). Waiting {retry_after}s...")
            time.sleep(retry_after)
            continue

        if response.status_code >= 500 and attempt < max_retries - 1:
            wait = 2 ** attempt
            print(f"Server error {response.status_code}. Retrying in {wait}s...")
            time.sleep(wait)
            continue

        print(f"Request failed: {response.status_code} {response.text[:200]}")
        response.raise_for_status()

    raise RuntimeError(f"Failed after {max_retries} retries: {url}")


def transform_pr_data(raw_pr):
    transformed_pr = {
        "pr_id": str(uuid.uuid4()),
        "repo_name": f"{raw_pr['base']['repo']['owner']['login']}/{raw_pr['base']['repo']['name']}",
        "pr_number": raw_pr['number'],
        "title": raw_pr['title'],
        "state": raw_pr['state'],
        "author": {
            "username": raw_pr['user']['login'],
            "id": raw_pr['user']['id'],
            "profile_url": raw_pr['user']['html_url']
        },
        "created_at": raw_pr['created_at'],
        "updated_at": raw_pr['updated_at'],
        "merged_at": raw_pr.get('merged_at'),
        "merged_by": {
            "username": raw_pr['merged_by']['login'] if raw_pr.get('merged_by') else None,
            "id": raw_pr['merged_by']['id'] if raw_pr.get('merged_by') else None,
            "profile_url": raw_pr['merged_by']['html_url'] if raw_pr.get('merged_by') else None
        } if raw_pr.get('merged_by') else None,
        "description": raw_pr['body'] or "",
        "labels": [label['name'] for label in raw_pr.get('labels', [])],
        "comments_count": raw_pr.get('comments', 0),
        "review_comments_count": raw_pr.get('review_comments', 0),
        "commits_count": raw_pr.get('commits', 0),
        "additions": raw_pr.get('additions', 0),
        "deletions": raw_pr.get('deletions', 0),
        "changed_files_count": raw_pr.get('changed_files', 0),
        "changed_files": [],
        "diff_url": raw_pr['diff_url'],
        "patch_url": raw_pr['patch_url'],
        "language_stats": {},
        "is_draft": raw_pr.get('draft', False)
    }
    return transformed_pr


def get_pr_files(pr_number):
    files_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/files"
    try:
        response = github_get(files_url)
        files_data = response.json()
        return [
            {
                "filename": file_info['filename'],
                "status": file_info['status'],
                "additions": file_info['additions'],
                "deletions": file_info['deletions']
            }
            for file_info in files_data
        ]
    except Exception as e:
        print(f"Error fetching files for PR {pr_number}: {e}")
    return []


def fetch_all_prs_by_state(state='all', per_page=100):
    all_prs = []
    page = 1
    max_pages = 50

    while page <= max_pages:
        params = {
            'state': state,
            'per_page': per_page,
            'page': page,
            'sort': 'created',
            'direction': 'asc',
        }

        print(f"Fetching page {page}... (collected so far: {len(all_prs)})")
        response = github_get(base_repo_url, params=params)
        page_prs = response.json()

        if not isinstance(page_prs, list):
            raise ValueError(f"Unexpected response on page {page}: {page_prs}")

        if not page_prs:
            break

        all_prs.extend(page_prs)
        page += 1
        time.sleep(0.5)

    return all_prs


print(f"Collecting PR data from {REPO_OWNER}/{REPO_NAME}...")
all_raw_pr_data = fetch_all_prs_by_state(state='all')

states_count = {}
merged_count = 0
for pr in all_raw_pr_data:
    state = pr['state']
    states_count[state] = states_count.get(state, 0) + 1
    if pr.get('merged_at'):
        merged_count += 1

print(f"Collected {len(all_raw_pr_data)} PRs")
print(f"Open: {states_count.get('open', 0)}, Closed: {states_count.get('closed', 0)}, Merged: {merged_count}")

print("Processing data...")
transformed_prs = [transform_pr_data(raw_pr) for raw_pr in all_raw_pr_data]

output_dir = os.path.join(OUTPUT_SUBDIR, "PR data for Developers")
os.makedirs(output_dir, exist_ok=True)

output_filename = os.path.join(output_dir, f"{REPO_OWNER.lower()}_all_pr_data.json")
with open(output_filename, 'w', encoding='utf-8') as json_file:
    json.dump(transformed_prs, json_file, indent=2, ensure_ascii=False)

print(f"Saved {len(transformed_prs)} PRs to {output_filename}")
print("Done!")
