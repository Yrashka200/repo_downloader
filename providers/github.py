"""GitHub provider."""

import os

from config import TOKEN_ENV
from core.http import RateLimitedClient
from providers.base import Provider, Repo


class GitHubProvider(Provider):
    name = "github"
    API = "https://api.github.com"

    def __init__(self) -> None:
        self.token = os.environ.get(TOKEN_ENV["github"])
        self.client = RateLimitedClient()

    def _headers(self) -> dict:
        headers = {
            "User-Agent": "repo-downloader",
            "Accept": "application/vnd.github+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_repos(
        self,
        username: str,
        skip_forks: bool = False,
        skip_archived: bool = False,
    ) -> list[Repo] | None:
        repos: list[Repo] = []
        page = 1
        while True:
            url = (
                f"{self.API}/users/{username}/repos"
                f"?per_page=100&page={page}&type=owner"
            )
            data = self.client.get_json(url, self._headers())
            if data is None:
                return None
            if not data:
                break

            for item in data:
                if skip_forks and item.get("fork", False):
                    continue
                if skip_archived and item.get("archived", False):
                    continue
                repos.append(Repo(
                    name=item["name"],
                    clone_url=item["clone_url"],
                    private=item.get("private", False),
                    default_branch=item.get("default_branch", "main"),
                    fork=item.get("fork", False),
                    archived=item.get("archived", False),
                ))

            if len(data) < 100:
                break
            page += 1

        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"https://github.com/{username}/{repo_name}.git"
