"""Global settings."""

# --- Download behaviour ---
DEFAULT_OUTPUT_DIR = "downloads"
CLONE_TIMEOUT = 600       
CLONE_DEPTH = 1          y

# Environment variables holding access tokens
TOKEN_ENV = {
    "github":  "GITHUB_TOKEN",
    "gitlab":  "GITLAB_TOKEN",
    "forgejo": "FORGEJO_TOKEN",
}

# --- Self-update ---
# GitHub repo that hosts this script (owner/repo)
UPSTREAM_REPO   = "yrashka200/repo_downloader"
UPSTREAM_BRANCH = "main"


LOCAL_VERSION_FILE = "version.txt"

# Paths that must never be touched by the updater
UPDATE_EXCLUDE = {
    ".git",
    "__pycache__",
    "downloads",
    "version.local",
    ".venv",
    "venv",
}
