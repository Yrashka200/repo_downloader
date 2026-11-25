"""GitHub provider."""

import json
import os
import urllib.error
import urllib.request

from config import TOKEN_ENV
from providers.base import Provider, Repo


class GitHubProvider(Provider):
    name = "github"
    API = "https://api.github.com"

    def __init__(self) -> None:
        self.token = os.environ.get(TOKEN_ENV["github"])

    def _headers(self) -> dict:
        headers = {
            "User-Agent": "repo-downloader",
            "Accept": "application/vnd.github+json",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_repos(self, username: str) -> list[Repo] | None:
        repos: list[Repo] = []
        page = 1
        while True:
            url = (
                f"{self.API}/users/{username}/repos"
                f"?per_page=100&page={page}&type=owner"
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
            page += 1
        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"https://github.com/{username}/{repo_name}.git"
