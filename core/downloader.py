"""Download orchestration: cloning, progress, stats."""

import os
import subprocess
import time

from config import CLONE_DEPTH, CLONE_TIMEOUT, DEFAULT_OUTPUT_DIR
from core.progress import ProgressTracker, format_time
from providers.base import Provider, Repo


def clone_repo(url: str, dest: str, timeout: int = CLONE_TIMEOUT) -> tuple[bool, str]:
    if os.path.exists(dest):
        return True, "already exists, skipped"

    cmd = ["git", "clone"]
    if CLONE_DEPTH:
        cmd += ["--depth", str(CLONE_DEPTH)]
    cmd += [url, dest]

    try:
        result = subprocess.run(
            cmd,
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
        print(f"[{i}/{len(repos)}] Cloning '{repo.name}'...")
        t0 = time.time()
        ok, msg = clone_repo(repo.clone_url, os.path.join(root, repo.name))
        elapsed = time.time() - t0

        if ok:
            success.append(repo.name)
            print(f"   OK ({format_time(elapsed)}, {msg or 'cloned'})")
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
