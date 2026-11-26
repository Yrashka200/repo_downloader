"""Abstract provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class Repo:
    name: str
    clone_url: str
    private: bool = False
    default_branch: str = "main"
    fork: bool = False
    archived: bool = False


class Provider(ABC):
    """Base class for all git hosting providers."""

    name: str = "base"

    @abstractmethod
    def fetch_repos(
        self,
        username: str,
        skip_forks: bool = False,
        skip_archived: bool = False,
    ) -> list[Repo] | None:
        """
        Return a list of repositories.
        None -> account unavailable (suspended / not found / banned).
        []   -> account exists but no repos match the filters.
        """

    @abstractmethod
    def build_clone_url(self, username: str, repo_name: str) -> str:
        """Construct a git clone URL from repo name (fallback path)."""

    def __str__(self) -> str:
        return self.name
