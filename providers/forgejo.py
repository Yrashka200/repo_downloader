"""Forgejo / Gitea provider (default: https://v15.next.forgejo.org/)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from config import TOKEN_ENV
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

    def _headers(self) -> dict:
        headers = {"User-Agent": "repo-downloader"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def fetch_repos(self, username: str) -> list[Repo] | None:
        repos: list[Repo] = []
        page = 1
        while True:
            url = (
                f"{self.base_url}/api/v1/users/"
                f"{urllib.parse.quote(username)}/repos"
                f"?limit=50&page={page}"
            )
            req = urllib.request.Request(url, headers=self._headers())
            try:
                with urllib.request.urlopen(req) as r:
                    data = json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                raise
            if not data:
                break
            for item in data:
                repos.append(Repo(
                    name=item["name"],
                    clone_url=item["clone_url"],
                    private=item.get("private", False),
                    default_branch=item.get("default_branch", "main"),
                ))
            if len(data) < 50:
                break
            page += 1
        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"{self.base_url}/{username}/{repo_name}.git"
