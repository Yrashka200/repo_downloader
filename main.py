"""Entry point: menu + orchestration."""

import shutil
import sys

from core.downloader import download_all
from core.fallback import ask_fallback
from providers import PROVIDERS


def logo():
    print(r"""
    ____  _____ ____  ____    ____  _        _______  _______  _______  ______   ______
   |  _ \| ____|  _ \/ __ \  |  _ \| |      / /  _  \|  _  \|  _  \|  _  \ /  __  \
   | |_) |  _| | |_) | |  | | | | | | |     / /| | | || |_) || |_) || |_) | |  |  |
   |  _ <| |___|  __/| |__| | | |_| | |___ / / | |_| ||  _ < |  _ < |  _ < |  |__| |
   |_| \_\_____|_|    \____/  |____/|_____/_/  \_____/|_| \_\|_| \_\|_| \_\ \______/
""")


def choose_provider():
    print("Where to download repositories from?\n")
    for key, (label, _) in PROVIDERS.items():
        extra = "  (https://v15.next.forgejo.org/)" if label == "Forgejo" else ""
        print(f"  {key}) {label}{extra}")
    print()

    while True:
        choice = input("Choose [1-3]: ").strip()
        if choice in PROVIDERS:
            label, cls = PROVIDERS[choice]
            print(f"\n-> Using {label}\n")
            return cls()
        print("Invalid choice, try again.")


def main() -> None:
    if shutil.which("git") is None:
        print("'git' is not installed or not in PATH.")
        sys.exit(1)

    logo()

    provider = choose_provider()

    username = input("Enter username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    print(f"\nFetching repos for '{username}' on {provider.name}...")
    repos = provider.fetch_repos(username)

    if repos is None:
        repos = ask_fallback(provider, username)
        if not repos:
            print("Cancelled.")
            sys.exit(0)
    elif not repos:
        print(f"No public repositories found for '{username}'.")
        sys.exit(0)

    print(f"Found {len(repos)} repositories.\n")
    result = download_all(provider, username, repos)

    print(f"\nAll done. Path: {result['output_dir']}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)
