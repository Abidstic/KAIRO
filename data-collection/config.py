import os
from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class CrawlerConfig:
    """Configuration for GitHub crawler"""
    
    github_token: str = os.environ.get('GH_TOKEN')
    base_url: str = 'https://api.github.com'
    
    max_requests_per_hour: int = 4800
    rate_limit_buffer: int = 200
    max_concurrent_requests: int = 10
    
    max_retries: int = 3
    base_backoff_delay: float = 60.0
    max_backoff_delay: float = 300.0
    
    base_folder: str = 'crawled-data'
    items_per_page: int = 100
    
    progress_update_interval: float = 1.0
    
    checkpoint_interval: int = 50
    
    crawl_limit: int = 0
    crawl_selection: str = 'latest'
    
    def __post_init__(self):
        if not self.github_token:
            raise ValueError("GitHub token is required. Set GH_TOKEN environment variable.")
    
    @property
    def headers(self) -> Dict[str, str]:
        """Standard GitHub API headers"""
        return {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {self.github_token}',
            'X-GitHub-Api-Version': '2022-11-28'
        }

config = CrawlerConfig()

CRAWLER_SEQUENCE = [
    'pull_requests',
    'commits',
    'pr_files',
    'pr_reviews',
    'pr_commits',
    'pr_comments',
    'single_commits',
]

PARALLEL_CRAWLERS = {
    'pr_dependencies': ['pr_files', 'pr_reviews', 'pr_commits', 'pr_comments']
}