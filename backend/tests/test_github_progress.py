from __future__ import annotations

import pytest

from app.core.exceptions import AppError
from app.services.github_progress import (
    format_github_progress_snapshot,
    parse_github_repo_url,
)


@pytest.mark.parametrize(
    ("repo_url", "full_name"),
    [
        ("https://github.com/openai/openai-python", "openai/openai-python"),
        ("github.com/vuejs/core", "vuejs/core"),
        ("git@github.com:fastapi/fastapi.git", "fastapi/fastapi"),
        ("https://github.com/owner/repo/tree/main", "owner/repo"),
    ],
)
def test_parse_github_repo_url_accepts_common_forms(repo_url: str, full_name: str) -> None:
    repo_ref = parse_github_repo_url(repo_url)

    assert repo_ref.full_name == full_name


def test_parse_github_repo_url_rejects_non_github_urls() -> None:
    with pytest.raises(AppError):
        parse_github_repo_url("https://gitlab.com/owner/repo")


def test_format_github_progress_snapshot_includes_repo_activity() -> None:
    text = format_github_progress_snapshot(
        {
            "repo_ref": {"owner": "owner", "repo": "repo"},
            "repository": {
                "full_name": "owner/repo",
                "description": "demo repo",
                "default_branch": "main",
                "pushed_at": "2026-07-24T10:00:00Z",
                "updated_at": "2026-07-24T10:30:00Z",
                "stargazers_count": 3,
                "forks_count": 1,
                "open_issues_count": 2,
            },
            "languages": {"Python": 80, "TypeScript": 20},
            "commits": [
                {
                    "sha": "abcdef123456",
                    "commit": {
                        "message": "Add GitHub progress analysis",
                        "author": {"name": "ma", "date": "2026-07-24T10:20:00Z"},
                    },
                }
            ],
            "pull_requests": [
                {
                    "number": 5,
                    "state": "open",
                    "title": "Wire GitHub API to DeepSeek",
                    "user": {"login": "ma"},
                    "updated_at": "2026-07-24T10:40:00Z",
                    "merged_at": None,
                }
            ],
            "issues": [
                {
                    "number": 8,
                    "state": "open",
                    "title": "Need repository progress report",
                    "user": {"login": "ma"},
                    "labels": [{"name": "enhancement"}],
                    "updated_at": "2026-07-24T10:50:00Z",
                }
            ],
        }
    )

    assert "仓库：owner/repo" in text
    assert "Add GitHub progress analysis" in text
    assert "Wire GitHub API to DeepSeek" in text
    assert "Need repository progress report" in text
