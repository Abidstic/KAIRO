import random
from typing import Dict, Any, List
from .base_crawler import BaseListCrawler
from config import config

class PullRequestsCrawler(BaseListCrawler):
    """Crawler for GitHub pull requests"""
    
    @property
    def crawler_name(self) -> str:
        return "pull_requests"
    
    @property
    def output_folder_path(self) -> str:
        return f"{self.base_folder_path}/pull"
    
    def get_api_method(self):
        """Get the GitHub client method for pull requests"""
        return self.github_client.get_pull_requests
    
    def get_api_params(self) -> Dict[str, Any]:
        """Parameters for pull requests API call"""
        return {}
    
    def filter_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply the crawl limiter: scope down to N PRs (latest/oldest/random)
        so everything downstream (commits, files, reviews, comments) stays
        relevant to the same coherent set of pull requests."""
        limit = config.crawl_limit
        
        if not limit or limit <= 0 or limit >= len(data):
            selected = data
        else:
            selection = config.crawl_selection
            
            if selection == 'random':
                selected = random.sample(data, limit)
            else:
                sorted_data = sorted(data, key=lambda pr: pr.get('created_at', ''))
                selected = sorted_data[-limit:] if selection == 'latest' else sorted_data[:limit]
            
            self.logger.info(
                f"Crawl limiter applied: keeping {len(selected)}/{len(data)} "
                f"pull requests ({selection})"
            )
        
        applied_limit = len(selected) if (limit and 0 < limit < len(data)) else 0
        self.checkpoint_manager.set_crawl_limit(applied_limit, config.crawl_selection)
        
        dates = [pr['created_at'] for pr in selected if pr.get('created_at')]
        if dates:
            self.checkpoint_manager.set_pr_date_range(min(dates), max(dates))
        
        return selected
    
    async def post_process_data(self, data: List[Dict[str, Any]]):
        """Post-process pull requests data to track PR numbers"""
        for pr in data:
            if 'number' in pr:
                self.checkpoint_manager.add_completed_pull_number(pr['number'])
        
        self.logger.info(f"Tracked {len(data)} pull request numbers for dependency crawlers")