"""Global settings."""

# --- Download behaviour ---
DEFAULT_OUTPUT_DIR = "downloads"
CLONE_TIMEOUT = 600       # seconds per repo
CLONE_DEPTH = 1           # use 1 for shallow clone; None for full history

# --- Filtering ---
SKIP_FORKS_DEFAULT = False
SKIP_ARCHIVED_DEFAULT = False

# --- Rate limiting ---
# Maximum requests per second to any provider API (0 = unlimited)
API_RATE_LIMIT_RPS = 2

# How many times to retry a request when the provider signals rate limiting
API_MAX_RETRIES = 3

# Base backoff in seconds when we cannot read a Retry-After / X-RateLimit-Reset
API_BACKOFF_BASE = 2.0

# Environment variables holding access tokens
TOKEN_ENV = {
    "github":  "GITHUB_TOKEN",
    "gitlab":  "GITLAB_TOKEN",
    "forgejo": "FORGEJO_TOKEN",
}

# --- Self-update ---
UPSTREAM_REPO   = "yrashka200/repo_downloader"
UPSTREAM_BRANCH = "main"
LOCAL_VERSION_FILE = "version.txt"
UPDATE_EXCLUDE = {
    ".git",
    "__pycache__",
    "downloads",
    "version.local",
    ".venv",
    "venv",
}
