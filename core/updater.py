"""Self-update from the upstream GitHub repository."""

import io
import json
import os
import shutil
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile

from config import (
    LOCAL_VERSION_FILE,
    UPSTREAM_BRANCH,
    UPSTREAM_REPO,
    UPDATE_EXCLUDE,
)


def _api_headers() -> dict:
    headers = {
        "User-Agent": "repo-downloader-updater",
        "Accept": "application/vnd.github+json",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def read_local_version() -> str:
    try:
        with open(LOCAL_VERSION_FILE, encoding="utf-8") as f:
            return f.read().strip()
    except OSError:
        return "0.0.0"


def fetch_remote_version() -> str | None:
    """Return the version string from upstream's version.txt, or None."""
    url = (
        f"https://api.github.com/repos/{UPSTREAM_REPO}/contents/"
        f"{LOCAL_VERSION_FILE}?ref={UPSTREAM_BRANCH}"
    )
    req = urllib.request.Request(url, headers=_api_headers())
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    except Exception:
        return None

    # GitHub returns base64-encoded content for small files
    import base64
    try:
        content = base64.b64decode(data["content"]).decode("utf-8")
        return content.strip()
    except Exception:
        return None


def _parse_version(v: str) -> tuple[int, ...]:
    """Turn '1.2.3' into (1, 2, 3). Non-numeric parts become 0."""
    parts = []
    for chunk in v.split("."):
        try:
            parts.append(int(chunk))
        except ValueError:
            parts.append(0)
    return tuple(parts)


def is_newer(remote: str, local: str) -> bool:
    return _parse_version(remote) > _parse_version(local)


def download_archive(dest_dir: str) -> str:
    """Download upstream branch zip into dest_dir. Return extracted root path."""
    url = (
        f"https://github.com/{UPSTREAM_REPO}/archive/refs/heads/"
        f"{UPSTREAM_BRANCH}.zip"
    )
    req = urllib.request.Request(url, headers=_api_headers())
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        zf.extractall(dest_dir)

    # GitHub zips contain a single top-level folder like "repo-main"
    entries = [
        os.path.join(dest_dir, name)
        for name in os.listdir(dest_dir)
        if os.path.isdir(os.path.join(dest_dir, name))
    ]
    if not entries:
        raise RuntimeError("archive is empty")
    return entries[0]


def sync_tree(src_root: str, dst_root: str) -> list[str]:
    """
    Copy files from src_root to dst_root, skipping excluded paths.
    Returns list of relative paths that were updated.
    """
    updated: list[str] = []

    for dirpath, dirnames, filenames in os.walk(src_root):
        dirnames[:] = [d for d in dirnames if d not in UPDATE_EXCLUDE]

        rel_dir = os.path.relpath(dirpath, src_root)
        if rel_dir == ".":
            rel_dir = ""
        dst_dir = os.path.join(dst_root, rel_dir) if rel_dir else dst_root
        os.makedirs(dst_dir, exist_ok=True)

        for fname in filenames:
            if fname in UPDATE_EXCLUDE:
                continue
            src_file = os.path.join(dirpath, fname)
            dst_file = os.path.join(dst_dir, fname)
            rel_file = os.path.relpath(src_file, src_root)

            if _same_file(src_file, dst_file):
                continue

            shutil.copy2(src_file, dst_file)
            updated.append(rel_file)

    return updated


def _same_file(a: str, b: str) -> bool:
    if not os.path.exists(b):
        return False
    try:
        return os.path.getsize(a) == os.path.getsize(b) and _sha(a) == _sha(b)
    except OSError:
        return False


def _sha(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check_for_updates(silent_if_none: bool = True) -> bool:
    """
    Check upstream for a newer version.
    If found, download and apply the update.
    Returns True if an update was applied.
    """
    local = read_local_version()
    remote = fetch_remote_version()

    if remote is None:
        if not silent_if_none:
            print("Could not reach upstream to check for updates.")
        return False

    if not is_newer(remote, local):
        if not silent_if_none:
            print(f"Already up to date (local {local}, remote {remote}).")
        return False

    print(f"New version available: {remote} (current: {local})")
    print("Downloading update...")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    tmp_dir = tempfile.mkdtemp(prefix="repo-downloader-update-")
    try:
        extracted = download_archive(tmp_dir)
        updated = sync_tree(extracted, project_root)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    # Write the new version marker
    try:
        with open(os.path.join(project_root, LOCAL_VERSION_FILE), "w",
                  encoding="utf-8") as f:
            f.write(remote + "\n")
    except OSError as e:
        print(f"Warning: could not write version file: {e}")

    if updated:
        print(f"Updated {len(updated)} file(s):")
        for path in updated:
            print(f"  - {path}")
    else:
        print("No files changed (version bumped only).")

    print("Update applied.")
    return True


def prompt_restart_if_needed(updated: bool) -> None:
    """Offer to relaunch the script so the new code takes effect."""
    if not updated:
        return
    answer = input("Restart now to use the new version? [y/N]: ").strip().lower()
    if answer == "y":
        os.execv(sys.executable, [sys.executable] + sys.argv)
