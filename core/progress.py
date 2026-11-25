"""Progress bar and time formatting."""

import time


def format_time(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


class ProgressTracker:
    """Computes ETA based on average time per repo."""

    def __init__(self, total: int) -> None:
        self.total = total
        self.done = 0
        self.start = time.time()
        self.times: list[float] = []

    def update(self, elapsed: float) -> str:
        self.done += 1
        self.times.append(elapsed)

        avg = sum(self.times) / len(self.times)
        remaining = self.total - self.done
        eta = avg * remaining
        total_elapsed = time.time() - self.start

        bar_len = 30
        filled = int(bar_len * self.done / self.total)
        bar = "#" * filled + "-" * (bar_len - filled)
        percent = self.done / self.total * 100

        return (
            f"   [{bar}] {self.done}/{self.total} ({percent:.1f}%) | "
            f"Elapsed: {format_time(total_elapsed)} | "
            f"ETA: {format_time(eta)}"
        )

    @property
    def total_elapsed(self) -> float:
        return time.time() - self.start
