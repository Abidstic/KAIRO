import json
import os
import time
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from datetime import datetime

API_TOKEN = os.environ.get("GH_TOKEN", "")
REPO_OWNER = 'fastify'
REPO_NAME = 'fastify'
MAX_PRS_TO_FETCH = 500
PR_FETCH_SORT = 'updated_at'
PR_FETCH_ORDER = 'desc'
PR_CUTOFF_DATE = '2025-11-01'
PR_CUTOFF_FIELD = 'updated_at'
PR_LIST_FILE = os.path.join('fastify', 'PR data for Developers', 'fastify_all_pr_data.json')
OUTPUT_DIR = os.path.join('fastify', 'PR data for Reviewers')
CHECKPOINT_FILE = 'reviewer_fetch_checkpoint_fastify_cutoff20251101.json'
CHECKPOINT_EVERY = 50
REQUEST_DELAY = 0.4
SPLIT_TRAIN_RATIO = 0.8
SPLIT_SORT_KEY = 'created_at'
AUTO_SPLIT = True


def make_github_request(url, max_retries=6):
    """Make a request to GitHub API with rate-limit retry."""
    for attempt in range(max_retries):
        req = urllib.request.Request(url)
        if API_TOKEN:
            req.add_header('Authorization', f'Bearer {API_TOKEN}')
        req.add_header('User-Agent', 'ReviewerDataCollector/1.0')
        req.add_header('Accept', 'application/vnd.github+json')
        req.add_header('X-GitHub-Api-Version', '2022-11-28')

        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < max_retries - 1:
                retry_after = int(e.headers.get('Retry-After', 60))
                print(f"Rate limited ({e.code}). Waiting {retry_after}s...")
                time.sleep(retry_after)
                continue
            print(f"HTTP error {e.code} for {url}: {e.read().decode()[:200]}")
            return None
        except Exception as e:
            print(f"Error making request to {url}: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return None
    return None


def get_pr_reviews(pr_number):
    reviews_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/reviews"
    reviews_data = make_github_request(reviews_url)
    if not reviews_data:
        return []

    reviews = []
    for review in reviews_data:
        if review.get('user') is None:
            continue
        reviews.append({
            "review_id": review['id'],
            "reviewer_username": review['user']['login'],
            "reviewer_id": review['user']['id'],
            "reviewer_profile_url": review['user']['html_url'],
            "reviewer_avatar_url": review['user']['avatar_url'],
            "reviewer_type": review['user']['type'],
            "state": review['state'],
            "body": review.get('body', ''),
            "submitted_at": review['submitted_at'],
            "commit_id": review.get('commit_id', ''),
            "html_url": review.get('html_url', ''),
            "author_association": review.get('author_association', '')
        })
    return reviews


def get_pr_review_comments(pr_number):
    comments_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/pulls/{pr_number}/comments"
    comments_data = make_github_request(comments_url)
    if not comments_data:
        return []

    comments = []
    for comment in comments_data:
        if comment.get('user') is None:
            continue
        comments.append({
            "comment_id": comment['id'],
            "reviewer_username": comment['user']['login'],
            "reviewer_id": comment['user']['id'],
            "reviewer_profile_url": comment['user']['html_url'],
            "body": comment.get('body', ''),
            "created_at": comment['created_at'],
            "updated_at": comment['updated_at'],
            "path": comment.get('path', ''),
            "line": comment.get('line'),
            "diff_hunk": comment.get('diff_hunk', ''),
            "html_url": comment.get('html_url', ''),
            "author_association": comment.get('author_association', ''),
            "in_reply_to_id": comment.get('in_reply_to_id')
        })
    return comments


def get_pr_general_comments(pr_number):
    comments_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/issues/{pr_number}/comments"
    comments_data = make_github_request(comments_url)
    if not comments_data:
        return []

    comments = []
    for comment in comments_data:
        if comment.get('user') is None:
            continue
        comments.append({
            "comment_id": comment['id'],
            "commenter_username": comment['user']['login'],
            "commenter_id": comment['user']['id'],
            "commenter_profile_url": comment['user']['html_url'],
            "body": comment.get('body', ''),
            "created_at": comment['created_at'],
            "updated_at": comment['updated_at'],
            "html_url": comment.get('html_url', ''),
            "author_association": comment.get('author_association', '')
        })
    return comments


def load_pr_list():
    if not os.path.exists(PR_LIST_FILE):
        raise FileNotFoundError(f"PR list not found: {PR_LIST_FILE}. Run DeveloperFeachData.py first.")
    with open(PR_LIST_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def apply_cutoff(pr_list):
    """Keep only PRs on/before PR_CUTOFF_DATE (end of that day UTC)."""
    if not PR_CUTOFF_DATE:
        return pr_list
    cutoff = f"{PR_CUTOFF_DATE}T23:59:59Z"
    filtered = [pr for pr in pr_list if pr.get(PR_CUTOFF_FIELD, '') <= cutoff]
    print(f"Cutoff {PR_CUTOFF_FIELD} <= {PR_CUTOFF_DATE}: {len(filtered)}/{len(pr_list)} PRs eligible")
    return filtered


def select_prs_to_fetch(pr_list):
    """Select newest PRs up to cutoff date, same strategy as Express."""
    pr_list = apply_cutoff(pr_list)
    reverse = PR_FETCH_ORDER == 'desc'
    sorted_prs = sorted(pr_list, key=lambda pr: pr.get(PR_FETCH_SORT, ''), reverse=reverse)
    if MAX_PRS_TO_FETCH > 0:
        return sorted_prs[:MAX_PRS_TO_FETCH]
    return sorted_prs


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed_pr_numbers": [], "reviewer_data": []}


def save_checkpoint(processed_pr_numbers, reviewer_data):
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "processed_pr_numbers": processed_pr_numbers,
            "reviewer_data": reviewer_data,
            "last_updated": datetime.now().isoformat()
        }, f, indent=2)


def build_pr_reviewer_record(pr_meta, reviews, review_comments, general_comments):
    return {
        "pr_id": str(uuid.uuid4()),
        "repo_name": f"{REPO_OWNER}/{REPO_NAME}",
        "pr_number": pr_meta['pr_number'],
        "title": pr_meta['title'],
        "state": pr_meta['state'],
        "author": pr_meta['author'],
        "created_at": pr_meta['created_at'],
        "updated_at": pr_meta['updated_at'],
        "merged_at": pr_meta.get('merged_at'),
        "merged_by": pr_meta.get('merged_by'),
        "description": pr_meta.get('description', ''),
        "labels": pr_meta.get('labels', []),
        "additions": pr_meta.get('additions', 0),
        "deletions": pr_meta.get('deletions', 0),
        "changed_files_count": pr_meta.get('changed_files_count', 0),
        "is_draft": pr_meta.get('is_draft', False),
        "reviews": reviews,
        "review_comments": review_comments,
        "general_comments": general_comments,
        "reviewer_summary": {
            "total_reviews": len(reviews),
            "total_review_comments": len(review_comments),
            "total_general_comments": len(general_comments),
            "unique_reviewers": list(set(
                [r['reviewer_username'] for r in reviews] +
                [c['reviewer_username'] for c in review_comments]
            )),
            "approval_count": len([r for r in reviews if r['state'] == 'APPROVED']),
            "changes_requested_count": len([r for r in reviews if r['state'] == 'CHANGES_REQUESTED']),
            "comment_only_count": len([r for r in reviews if r['state'] == 'COMMENTED'])
        }
    }


def fetch_prs_with_reviewer_data():
    pr_list = select_prs_to_fetch(load_pr_list())

    checkpoint = load_checkpoint()
    processed = set(checkpoint.get('processed_pr_numbers', []))
    all_reviewer_data = checkpoint.get('reviewer_data', [])

    print(f"Selected {len(pr_list)} PRs from {PR_LIST_FILE}")
    print(f"Selection: {PR_FETCH_SORT} ({PR_FETCH_ORDER}) — same strategy as Express")
    if pr_list:
        print(f"Updated range: {pr_list[-1]['updated_at'][:10]} to {pr_list[0]['updated_at'][:10]}")
    print(f"Resuming with {len(processed)} PRs already processed")

    for index, pr_meta in enumerate(pr_list, start=1):
        pr_number = pr_meta['pr_number']
        if pr_number in processed:
            continue

        print(f"[{index}/{len(pr_list)}] Processing PR #{pr_number}: {pr_meta['title'][:60]}...")
        reviews = get_pr_reviews(pr_number)
        time.sleep(REQUEST_DELAY)
        review_comments = get_pr_review_comments(pr_number)
        time.sleep(REQUEST_DELAY)
        general_comments = get_pr_general_comments(pr_number)
        time.sleep(REQUEST_DELAY)

        if reviews or review_comments:
            pr_reviewer_data = build_pr_reviewer_record(
                pr_meta, reviews, review_comments, general_comments
            )
            all_reviewer_data.append(pr_reviewer_data)
            reviewer_count = len(pr_reviewer_data['reviewer_summary']['unique_reviewers'])
            print(f"    Found {len(reviews)} reviews, {len(review_comments)} review comments from {reviewer_count} reviewers")
        else:
            print("    No reviewer activity found")

        processed.add(pr_number)
        if len(processed) % CHECKPOINT_EVERY == 0:
            save_checkpoint(sorted(processed), all_reviewer_data)
            print(f"    Checkpoint saved ({len(processed)} PRs processed, {len(all_reviewer_data)} with reviewer activity)")

    save_checkpoint(sorted(processed), all_reviewer_data)
    all_reviewer_data.sort(key=lambda pr: pr.get(SPLIT_SORT_KEY, ''))
    return all_reviewer_data


def analyze_reviewer_patterns(reviewer_data):
    reviewer_profiles = defaultdict(lambda: {
        'username': '',
        'profile_url': '',
        'avatar_url': '',
        'user_id': None,
        'total_prs_reviewed': 0,
        'total_formal_reviews': 0,
        'total_review_comments': 0,
        'total_general_comments': 0,
        'review_states': {
            'APPROVED': 0,
            'CHANGES_REQUESTED': 0,
            'COMMENTED': 0,
            'DISMISSED': 0
        },
        'author_associations': defaultdict(int),
        'prs_reviewed': [],
        'review_activity_by_month': defaultdict(int),
        'repositories_reviewed': set(),
    })

    for pr_data in reviewer_data:
        repo_name = pr_data['repo_name']
        pr_number = pr_data['pr_number']

        for review in pr_data['reviews']:
            username = review['reviewer_username']
            profile = reviewer_profiles[username]
            profile['username'] = username
            profile['profile_url'] = review['reviewer_profile_url']
            profile['avatar_url'] = review['reviewer_avatar_url']
            profile['user_id'] = review['reviewer_id']
            profile['total_formal_reviews'] += 1
            profile['review_states'][review['state']] += 1
            profile['author_associations'][review['author_association']] += 1
            if pr_number not in profile['prs_reviewed']:
                profile['prs_reviewed'].append(pr_number)
                profile['total_prs_reviewed'] += 1
            profile['repositories_reviewed'].add(repo_name)
            review_date = datetime.fromisoformat(review['submitted_at'].replace('Z', '+00:00'))
            profile['review_activity_by_month'][review_date.strftime('%Y-%m')] += 1

        for comment in pr_data['review_comments']:
            username = comment['reviewer_username']
            profile = reviewer_profiles[username]
            profile['username'] = username
            profile['profile_url'] = comment['reviewer_profile_url']
            profile['user_id'] = comment['reviewer_id']
            profile['total_review_comments'] += 1
            if pr_number not in profile['prs_reviewed']:
                profile['prs_reviewed'].append(pr_number)
                profile['total_prs_reviewed'] += 1
            profile['repositories_reviewed'].add(repo_name)

        reviewer_usernames = set(
            [r['reviewer_username'] for r in pr_data['reviews']] +
            [c['reviewer_username'] for c in pr_data['review_comments']]
        )
        for comment in pr_data['general_comments']:
            username = comment['commenter_username']
            if username in reviewer_usernames:
                reviewer_profiles[username]['total_general_comments'] += 1

    for profile in reviewer_profiles.values():
        profile['repositories_reviewed'] = list(profile['repositories_reviewed'])
        profile['author_associations'] = dict(profile['author_associations'])
        profile['review_activity_by_month'] = dict(profile['review_activity_by_month'])

    return dict(reviewer_profiles)


def main():
    print("=" * 60)
    print("GITHUB REVIEWER DATA COLLECTOR")
    print("=" * 60)
    print(f"Target Repository: {REPO_OWNER}/{REPO_NAME}")
    print(f"PR source file: {PR_LIST_FILE}")
    print(f"Max PRs to analyze: {'all' if MAX_PRS_TO_FETCH == 0 else MAX_PRS_TO_FETCH}")
    print(f"Cutoff date: {PR_CUTOFF_DATE or 'none'} ({PR_CUTOFF_FIELD})")
    print(f"Split: {int(SPLIT_TRAIN_RATIO * 100)}/{int((1 - SPLIT_TRAIN_RATIO) * 100)} by {SPLIT_SORT_KEY} (oldest -> train, newest -> test)")
    print()

    reviewer_data = fetch_prs_with_reviewer_data()
    if not reviewer_data:
        print("No reviewer data collected. Exiting.")
        return

    print(f"\nCollected data from {len(reviewer_data)} PRs with reviewer activity")
    print("Analyzing reviewer patterns...")
    reviewer_profiles = analyze_reviewer_patterns(reviewer_data)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_data = {
        'metadata': {
            'repository': f"{REPO_OWNER}/{REPO_NAME}",
            'collection_date': timestamp,
            'total_prs_analyzed': len(reviewer_data),
            'total_reviewers_found': len(reviewer_profiles),
            'collection_parameters': {
                'max_prs_fetched': MAX_PRS_TO_FETCH,
                'pr_list_file': PR_LIST_FILE,
                'pr_fetch_sort': PR_FETCH_SORT,
                'pr_fetch_order': PR_FETCH_ORDER,
                'pr_cutoff_date': PR_CUTOFF_DATE,
                'pr_cutoff_field': PR_CUTOFF_FIELD,
                'split_train_ratio': SPLIT_TRAIN_RATIO,
                'split_sort': SPLIT_SORT_KEY,
                'api_token_used': API_TOKEN[:20] + "..." if API_TOKEN else "None"
            }
        },
        'pr_reviewer_data': reviewer_data,
        'reviewer_profiles': reviewer_profiles
    }

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_filename = f'{REPO_OWNER}_{REPO_NAME}_reviewer_data.json'
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\nData saved to: {output_path}")
    if reviewer_data:
        print(
            f"Chronological range ({SPLIT_SORT_KEY}): "
            f"{reviewer_data[0][SPLIT_SORT_KEY][:10]} to {reviewer_data[-1][SPLIT_SORT_KEY][:10]}"
        )

    if AUTO_SPLIT:
        from split_pr_data import split_pr_data
        print(f"\nSplitting into {int(SPLIT_TRAIN_RATIO * 100)}/{int((1 - SPLIT_TRAIN_RATIO) * 100)} train/test...")
        split_paths = split_pr_data(output_path, train_ratio=SPLIT_TRAIN_RATIO)
        for split_path in split_paths:
            print(f"  -> {split_path}")

    total_reviews = sum(len(pr['reviews']) for pr in reviewer_data)
    total_review_comments = sum(len(pr['review_comments']) for pr in reviewer_data)
    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)
    print(f"PRs with reviewer activity: {len(reviewer_data)}")
    print(f"Total formal reviews: {total_reviews}")
    print(f"Total review comments: {total_review_comments}")
    print(f"Unique reviewers found: {len(reviewer_profiles)}")

    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        print("Checkpoint file removed after successful completion.")


if __name__ == "__main__":
    main()
