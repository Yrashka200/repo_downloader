"""Global settings."""

DEFAULT_OUTPUT_DIR = "downloads"
CLONE_TIMEOUT = 600       # seconds per repo
CLONE_DEPTH = 1           # use 1 for shallow clone; None for full history

# Environment variables holding access tokens
TOKEN_ENV = {
    "github":  "GITHUB_TOKEN",
    "gitlab":  "GITLAB_TOKEN",
    "forgejo": "FORGEJO_TOKEN",
}
