"""Provider registry."""

from providers.github import GitHubProvider
from providers.gitlab import GitLabProvider
from providers.forgejo import ForgejoProvider


PROVIDERS = {
    "1": ("GitHub",  GitHubProvider),
    "2": ("GitLab",  GitLabProvider),
    "3": ("Forgejo", ForgejoProvider),  # https://v15.next.forgejo.org/
}
