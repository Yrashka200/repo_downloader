"""Fallback: manual repo list when the API is unavailable (e.g. suspended account)."""

from providers.base import Provider, Repo


def load_names_from_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [
            line.strip()
            for line in f
            if line.strip() and not line.startswith("#")
        ]


def ask_fallback(provider: Provider, username: str) -> list[Repo] | None:
    """Ask the user how to obtain repo names manually."""
    print(f"API returned 404 for '{username}' on {provider.name}.")
    print("Account may be suspended, private, or nonexistent.\n")
    print("Options:")
    print("  1) File with repo names (one per line)")
    print("  2) Repo names as a space-separated list")
    print("  3) Cancel\n")

    choice = input("Choose [1/2/3]: ").strip()

    if choice == "1":
        path = input("Path to file: ").strip()
        try:
            names = load_names_from_file(path)
        except OSError as e:
            print(f"Cannot read file: {e}")
            return None
    elif choice == "2":
        raw = input("Repo names: ").strip()
        names = raw.split()
    else:
        return None

    return [
        Repo(name=n, clone_url=provider.build_clone_url(username, n))
        for n in names
    ]
