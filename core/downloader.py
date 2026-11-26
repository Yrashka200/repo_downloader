"""Download orchestration: cloning / fetching, progress, stats."""

import os
import subprocess
import time

from config import CLONE_DEPTH, CLONE_TIMEOUT, DEFAULT_OUTPUT_DIR
from core.progress import ProgressTracker, format_time
from providers.base import Provider, Repo


def _run_git(args: list[str], timeout: int = CLONE_TIMEOUT) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
        if result.returncode != 0:
            err = result.stderr.decode(errors="ignore").strip()[:200]
            return False, err
        return True, ""
    except subprocess.TimeoutExpired:
        return False, f"timeout after {timeout}s"
    except Exception as e:
        return False, str(e)


def _is_git_repo(path: str) -> bool:
    return os.path.isdir(os.path.join(path, ".git"))


def sync_repo(url: str, dest: str, timeout: int = CLONE_TIMEOUT) -> tuple[bool, str]:
    """
    Clone if missing, otherwise update an existing checkout via fetch + ff-only merge.
    Returns (ok, message).
    """
    if not os.path.exists(dest):
        cmd = ["git", "clone"]
        if CLONE_DEPTH:
            cmd += ["--depth", str(CLONE_DEPTH)]
        cmd += [url, dest]
        ok, msg = _run_git(cmd, timeout)
        return ok, (msg or "cloned")

    if not _is_git_repo(dest):
        return False, "path exists but is not a git repository; skipped"

    # Existing repo: fetch and fast-forward if possible
    ok, msg = _run_git(["git", "-C", dest, "fetch", "--prune", "origin"], timeout)
    if not ok:
        return False, f"fetch failed: {msg}"

    # Determine current branch
    ok, out = _run_git(["git", "-C", dest, "rev-parse", "--abbrev-ref", "HEAD"], timeout)
    if not ok:
        return False, f"cannot detect branch: {out}"
    branch = out.strip() or "HEAD"

    if branch == "HEAD":
        # Detached HEAD; nothing safe to fast-forward
        return True, "fetched (detached HEAD, not merged)"

    ok, msg = _run_git(
        ["git", "-C", dest, "merge", "--ff-only", f"origin/{branch}"],
        timeout,
    )
    if not ok:
        return False, f"not fast-forwardable: {msg}"

    return True, "fetched and fast-forwarded"


def download_all(
    provider: Provider,
    username: str,
    repos: list[Repo],
    output_dir: str = DEFAULT_OUTPUT_DIR,
) -> dict:
    root = os.path.join(output_dir, provider.name, username)
    os.makedirs(root, exist_ok=True)
    print(f"Saving to: {os.path.abspath(root)}\n")

    tracker = ProgressTracker(len(repos))
    success: list[str] = []
    failed: list[tuple[str, str]] = []

    for i, repo in enumerate(repos, 1):
        existed = os.path.exists(os.path.join(root, repo.name))
        action = "Updating" if existed else "Cloning"
        print(f"[{i}/{len(repos)}] {action} '{repo.name}'...")

        t0 = time.time()
        ok, msg = sync_repo(repo.clone_url, os.path.join(root, repo.name))
        elapsed = time.time() - t0

        if ok:
            success.append(repo.name)
            print(f"   OK ({format_time(elapsed)}, {msg})")
        else:
            failed.append((repo.name, msg))
            print(f"   FAILED: {msg}")

        print(tracker.update(elapsed))
        print()

    print("=" * 60)
    print(f"Done in {format_time(tracker.total_elapsed)}")
    print(f"Success: {len(success)}/{len(repos)}")
    if failed:
        print(f"Failed:  {len(failed)}")
        for name, why in failed:
            print(f"  - {name}: {why}")

    return {
        "output_dir": os.path.abspath(root),
        "success": success,
        "failed": failed,
        "elapsed": tracker.total_elapsed,
    }
