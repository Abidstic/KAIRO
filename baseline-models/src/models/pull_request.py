from dataclasses import dataclass
from typing import List


@dataclass
class PullRequest:
    number: int
    file_paths: List[str]
    date: str
    developer_username: str
