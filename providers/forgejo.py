"""Forgejo / Gitea provider (default: https://v15.next.forgejo.org/)."""

import os
import urllib.parse

from config import TOKEN_ENV
from core.http import RateLimitedClient
from providers.base import Provider, Repo


class ForgejoProvider(Provider):
    name = "forgejo"

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (
            base_url
            or os.environ.get("FORGEJO_URL")
            or "https://v15.next.forgejo.org"
        ).rstrip("/")
        self.token = os.environ.get(TOKEN_ENV["forgejo"])
        self.client = RateLimitedClient()

    def _headers(self) -> dict:
        headers = {"User-Agent": "repo-downloader"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
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
                f"{self.base_url}/api/v1/users/"
                f"{urllib.parse.quote(username)}/repos"
                f"?limit=50&page={page}"
            )
            data = self.client.get_json(url, self._headers())
            if data is None:
                return None
            if not data:
                break

            for item in data:
                is_fork = bool(item.get("fork", False))
                is_archived = bool(item.get("archived", False))
                if skip_forks and is_fork:
                    continue
                if skip_archived and is_archived:
                    continue
                repos.append(Repo(
                    name=item["name"],
                    clone_url=item["clone_url"],
                    private=item.get("private", False),
                    default_branch=item.get("default_branch", "main"),
                    fork=is_fork,
                    archived=is_archived,
                ))

            if len(data) < 50:
                break
            page += 1

        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"{self.base_url}/{username}/{repo_name}.git"
