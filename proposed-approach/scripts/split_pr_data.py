"""Split PR data into train/test sets in chronological order (default 90/10)."""

import json
import sys
from pathlib import Path


TRAIN_RATIO = 0.9
SPLIT_SORT_KEY = "created_at"
SPLIT_METADATA_KEYS = {
    "split_type",
    "split_ratio",
    "split_sort",
    "total_prs_in_split",
    "total_reviewers_in_split",
}


def load_prs(data):
    if isinstance(data, list):
        return data, "developer"
    if isinstance(data, dict) and "pr_reviewer_data" in data:
        return data["pr_reviewer_data"], "reviewer"
    raise ValueError("Unsupported JSON format: expected a PR list or reviewer data object.")


def count_reviewers(prs):
    reviewers = set()
    for pr in prs:
        for review in pr.get("reviews", []):
            username = review.get("reviewer_username")
            if username:
                reviewers.add(username)
    return len(reviewers)


def output_path_for(input_path, split_type, data_type):
    stem = input_path.stem
    if data_type == "developer":
        if stem.endswith("_all_pr_data_complete"):
            base = stem.replace("_all_pr_data_complete", "")
            return input_path.with_name(f"{base}_{split_type}_data.json")
        if "_all_pr_data" in stem:
            base = stem.replace("_all_pr_data", "_pr_data")
            return input_path.with_name(f"{base}_{split_type}.json")
    return input_path.with_name(f"{stem}_{split_type}.json")


def build_output(data, data_type, split_type, split_prs, split_ratio):
    if data_type == "developer":
        return split_prs

    base_metadata = {
        key: value
        for key, value in data["metadata"].items()
        if key not in SPLIT_METADATA_KEYS
    }
    return {
        "metadata": {
            **base_metadata,
            "split_type": split_type,
            "split_ratio": split_ratio,
            "split_sort": SPLIT_SORT_KEY,
            "total_prs_in_split": len(split_prs),
            "total_reviewers_in_split": count_reviewers(split_prs),
        },
        "pr_reviewer_data": split_prs,
    }


def split_pr_data(input_path, train_ratio=TRAIN_RATIO):
    input_path = Path(input_path)
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    prs, data_type = load_prs(data)
    prs = sorted(prs, key=lambda pr: pr.get(SPLIT_SORT_KEY, ""))
    split_idx = int(len(prs) * train_ratio)

    splits = [
        ("train", prs[:split_idx], train_ratio),
        ("test", prs[split_idx:], 1 - train_ratio),
    ]

    output_paths = []
    for split_type, split_prs, split_ratio in splits:
        output = build_output(data, data_type, split_type, split_prs, split_ratio)
        output_path = output_path_for(input_path, split_type, data_type)

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        output_paths.append(output_path)
        if split_prs:
            print(
                f"{split_type}: {len(split_prs)} PRs -> {output_path.name} "
                f"({SPLIT_SORT_KEY}: {split_prs[0][SPLIT_SORT_KEY][:10]} to {split_prs[-1][SPLIT_SORT_KEY][:10]})"
            )
        else:
            print(f"{split_type}: 0 PRs -> {output_path.name}")

    return output_paths


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python split_pr_data.py <input.json> [train_ratio]")
        print("Example:")
        print('  python split_pr_data.py "npm_cli/PR data for Reviewers/npm_cli_reviewer_data.json" 0.9')
        sys.exit(1)

    ratio = float(sys.argv[2]) if len(sys.argv) > 2 else TRAIN_RATIO
    split_pr_data(sys.argv[1], train_ratio=ratio)
