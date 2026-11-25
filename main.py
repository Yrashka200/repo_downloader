"""Entry point: menu + orchestration."""

import argparse
import shutil
import sys

from core.downloader import download_all
from core.fallback import ask_fallback
from core.updater import check_for_updates, prompt_restart_if_needed
from providers import PROVIDERS


def logo():
    print(r"""
  ==========================================
   REPO DOWNLOADER
   GitHub / GitLab / Forgejo
  ==========================================
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download all available repositories of a user."
    )
    parser.add_argument(
        "--check-updates",
        action="store_true",
        help="Check for updates and exit (no downloads).",
    )
    parser.add_argument(
        "--no-update-check",
        action="store_true",
        help="Skip the automatic update check at startup.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.check_updates:
        check_for_updates(silent_if_none=False)
        sys.exit(0)

    if not args.no_update_check:
        try:
            updated = check_for_updates(silent_if_none=True)
        except Exception as e:
            print(f"Update check failed: {e}")
            updated = False
        if updated:
            prompt_restart_if_needed(updated)

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
