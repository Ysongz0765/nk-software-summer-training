from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

import httpx

from app.core.exceptions import AIServiceUnavailableError, AppError

JsonObject = dict[str, Any]


@dataclass(frozen=True)
class GitHubRepoRef:
    owner: str
    repo: str

    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"


class GitHubProgressService:
    def __init__(
        self,
        *,
        api_token: str | None = None,
        base_url: str = "https://api.github.com",
        timeout_seconds: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_token = (api_token or "").strip()
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._client = client

    async def fetch_progress_snapshot(
        self,
        repo_url: str,
        *,
        max_items: int = 10,
    ) -> JsonObject:
        repo_ref = parse_github_repo_url(repo_url)
        item_limit = max(1, min(max_items, 30))
        headers = self._headers()

        async def run(client: httpx.AsyncClient) -> JsonObject:
            repo_path = f"/repos/{repo_ref.full_name}"
            repo_data, commits, issues, pulls, languages = await asyncio.gather(
                self._get_json(client, repo_path, headers=headers),
                self._get_json(
                    client,
                    f"{repo_path}/commits",
                    headers=headers,
                    params={"per_page": item_limit},
                ),
                self._get_json(
                    client,
                    f"{repo_path}/issues",
                    headers=headers,
                    params={
                        "state": "all",
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": item_limit,
                    },
                ),
                self._get_json(
                    client,
                    f"{repo_path}/pulls",
                    headers=headers,
                    params={
                        "state": "all",
                        "sort": "updated",
                        "direction": "desc",
                        "per_page": item_limit,
                    },
                ),
                self._get_json(client, f"{repo_path}/languages", headers=headers),
            )
            return {
                "repo_ref": {"owner": repo_ref.owner, "repo": repo_ref.repo},
                "repository": repo_data,
                "commits": _ensure_list(commits),
                "issues": [
                    issue
                    for issue in _ensure_list(issues)
                    if isinstance(issue, Mapping) and "pull_request" not in issue
                ],
                "pull_requests": _ensure_list(pulls),
                "languages": languages if isinstance(languages, dict) else {},
                "fetched_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
            }

        if self._client is not None:
            return await run(self._client)

        async with httpx.AsyncClient(timeout=self._timeout_seconds) as client:
            return await run(client)

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ReportFlow-AI",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self._api_token:
            headers["Authorization"] = f"Bearer {self._api_token}"
        return headers

    async def _get_json(
        self,
        client: httpx.AsyncClient,
        path: str,
        *,
        headers: dict[str, str],
        params: dict[str, object] | None = None,
    ) -> Any:
        try:
            response = await client.get(f"{self._base_url}{path}", headers=headers, params=params)
        except httpx.HTTPError as exc:
            raise AIServiceUnavailableError("GitHub API request failed") from exc

        if response.status_code == 404:
            raise AppError("GitHub repository not found or not accessible")
        if response.status_code == 403:
            message = _github_error_message(response)
            raise AIServiceUnavailableError(f"GitHub API access denied: {message}")
        if response.status_code >= 400:
            message = _github_error_message(response)
            raise AIServiceUnavailableError(
                f"GitHub API returned HTTP {response.status_code}: {message}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise AIServiceUnavailableError("GitHub API returned invalid JSON") from exc


def parse_github_repo_url(repo_url: str) -> GitHubRepoRef:
    raw_value = repo_url.strip()
    if not raw_value:
        raise AppError("GitHub repository URL is required")

    if raw_value.startswith("git@github.com:"):
        path = raw_value.removeprefix("git@github.com:")
    elif raw_value.startswith("github.com/"):
        path = raw_value.removeprefix("github.com/")
    else:
        parsed = urlparse(raw_value)
        if parsed.netloc.lower() != "github.com":
            raise AppError("only github.com repository URLs are supported")
        path = parsed.path.lstrip("/")

    parts = [part for part in path.split("/") if part]
    if len(parts) < 2:
        raise AppError("GitHub repository URL must include owner and repository name")

    owner = parts[0].strip()
    repo = parts[1].removesuffix(".git").strip()
    if not owner or not repo:
        raise AppError("GitHub repository URL must include owner and repository name")
    return GitHubRepoRef(owner=owner, repo=repo)


def format_github_progress_snapshot(snapshot: JsonObject) -> str:
    repo = _as_mapping(snapshot.get("repository"))
    repo_ref = _as_mapping(snapshot.get("repo_ref"))
    languages = _as_mapping(snapshot.get("languages"))
    commits = _ensure_list(snapshot.get("commits"))
    issues = _ensure_list(snapshot.get("issues"))
    pull_requests = _ensure_list(snapshot.get("pull_requests"))

    lines = [
        "GitHub 项目进度分析素材",
        f"仓库：{repo.get('full_name') or _repo_full_name(repo_ref)}",
        f"描述：{repo.get('description') or '无'}",
        f"默认分支：{repo.get('default_branch') or 'unknown'}",
        f"最近推送：{repo.get('pushed_at') or 'unknown'}",
        f"更新时间：{repo.get('updated_at') or 'unknown'}",
        (
            "统计："
            f"stars={repo.get('stargazers_count', 0)}, "
            f"forks={repo.get('forks_count', 0)}, "
            f"open_issues={repo.get('open_issues_count', 0)}"
        ),
        f"主要语言：{_format_languages(languages)}",
        "",
        "最近提交：",
        *_format_commits(commits),
        "",
        "最近 Pull Requests：",
        *_format_pull_requests(pull_requests),
        "",
        "最近 Issues：",
        *_format_issues(issues),
    ]
    return "\n".join(lines)


def _format_commits(commits: list[Any]) -> list[str]:
    if not commits:
        return ["- 暂无可见提交"]
    lines: list[str] = []
    for item in commits:
        commit = _as_mapping(item)
        commit_body = _as_mapping(commit.get("commit"))
        author = _as_mapping(commit_body.get("author"))
        message = str(commit_body.get("message") or "").splitlines()[0]
        lines.append(
            "- "
            f"{str(commit.get('sha') or '')[:7]} "
            f"{author.get('date') or 'unknown'} "
            f"{author.get('name') or 'unknown'}：{message or '无提交说明'}"
        )
    return lines


def _format_pull_requests(pull_requests: list[Any]) -> list[str]:
    if not pull_requests:
        return ["- 暂无可见 PR"]
    lines: list[str] = []
    for item in pull_requests:
        pr = _as_mapping(item)
        user = _as_mapping(pr.get("user"))
        lines.append(
            "- "
            f"#{pr.get('number')} [{pr.get('state')}] "
            f"{pr.get('title') or '无标题'}；"
            f"作者={user.get('login') or 'unknown'}；"
            f"更新={pr.get('updated_at') or 'unknown'}；"
            f"合并={bool(pr.get('merged_at'))}"
        )
    return lines


def _format_issues(issues: list[Any]) -> list[str]:
    if not issues:
        return ["- 暂无可见 issue"]
    lines: list[str] = []
    for item in issues:
        issue = _as_mapping(item)
        user = _as_mapping(issue.get("user"))
        labels = [
            str(_as_mapping(label).get("name"))
            for label in _ensure_list(issue.get("labels"))
            if _as_mapping(label).get("name")
        ]
        lines.append(
            "- "
            f"#{issue.get('number')} [{issue.get('state')}] "
            f"{issue.get('title') or '无标题'}；"
            f"负责人={user.get('login') or 'unknown'}；"
            f"标签={', '.join(labels) if labels else '无'}；"
            f"更新={issue.get('updated_at') or 'unknown'}"
        )
    return lines


def _format_languages(languages: Mapping[str, Any]) -> str:
    if not languages:
        return "unknown"
    total = sum(value for value in languages.values() if isinstance(value, int | float))
    if total <= 0:
        return ", ".join(languages.keys())
    pairs: list[str] = []
    for name, value in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]:
        if isinstance(value, int | float):
            pairs.append(f"{name} {value / total:.0%}")
    return ", ".join(pairs) if pairs else ", ".join(languages.keys())


def _github_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text[:300] or "unknown error"
    if isinstance(data, Mapping) and isinstance(data.get("message"), str):
        return data["message"]
    return "unknown error"


def _repo_full_name(repo_ref: Mapping[str, Any]) -> str:
    owner = repo_ref.get("owner") or "unknown"
    repo = repo_ref.get("repo") or "unknown"
    return f"{owner}/{repo}"


def _ensure_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
