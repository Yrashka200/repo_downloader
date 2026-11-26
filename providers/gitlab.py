"""GitLab provider (supports self-hosted via GITLAB_URL)."""

import os
import urllib.parse

from config import TOKEN_ENV
from core.http import RateLimitedClient
from providers.base import Provider, Repo


class GitLabProvider(Provider):
    name = "gitlab"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url
            or os.environ.get("GITLAB_URL")
            or "https://gitlab.com"
        ).rstrip("/")
        self.token = os.environ.get(TOKEN_ENV["gitlab"])
        self.client = RateLimitedClient()

    def _headers(self) -> dict:
        headers = {"User-Agent": "repo-downloader"}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def fetch_repos(
        self,
        username: str,
        skip_forks: bool = False,
        skip_archived: bool = False,
    ) -> list[Repo] | None:
        user_url = (
            f"{self.base_url}/api/v4/users"
            f"?username={urllib.parse.quote(username)}"
        )
        users = self.client.get_json(user_url, self._headers())
        if users is None or not users:
            return None

        user_id = users[0]["id"]
        repos: list[Repo] = []
        page = 1
        while True:
            url = (
                f"{self.base_url}/api/v4/users/{user_id}/projects"
                f"?per_page=100&page={page}"
            )
            data = self.client.get_json(url, self._headers())
            if data is None:
                return None
            if not data:
                break

            for item in data:
                if skip_forks and item.get("forked_from_project"):
                    continue
                if skip_archived and item.get("archived", False):
                    continue
                repos.append(Repo(
                    name=item["path"],
                    clone_url=item["http_url_to_repo"],
                    private=item.get("visibility") != "public",
                    default_branch=item.get("default_branch", "main"),
                    fork=bool(item.get("forked_from_project")),
                    archived=item.get("archived", False),
                ))

            if len(data) < 100:
                break
            page += 1

        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"{self.base_url}/{username}/{repo_name}.git"
