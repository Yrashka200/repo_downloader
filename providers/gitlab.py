"""GitLab provider (supports self-hosted via GITLAB_URL)."""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from config import TOKEN_ENV
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

    def _headers(self) -> dict:
        headers = {"User-Agent": "repo-downloader"}
        if self.token:
            headers["PRIVATE-TOKEN"] = self.token
        return headers

    def fetch_repos(self, username: str) -> list[Repo] | None:
        # Verify the user exists first
        user_url = (
            f"{self.base_url}/api/v4/users"
            f"?username={urllib.parse.quote(username)}"
        )
        req = urllib.request.Request(user_url, headers=self._headers())
        try:
            with urllib.request.urlopen(req) as r:
                users = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            raise
        if not users:
            return None

        user_id = users[0]["id"]
        repos: list[Repo] = []
        page = 1
        while True:
            url = (
                f"{self.base_url}/api/v4/users/{user_id}/projects"
                f"?per_page=100&page={page}"
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
                    name=item["path"],
                    clone_url=item["http_url_to_repo"],
                    private=item.get("visibility") != "public",
                    default_branch=item.get("default_branch", "main"),
                ))
            page += 1
        return repos

    def build_clone_url(self, username: str, repo_name: str) -> str:
        return f"{self.base_url}/{username}/{repo_name}.git"
