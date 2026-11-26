"""Shared HTTP helper: rate limiting, retries, and respect for provider limits."""

import json
import time
import urllib.error
import urllib.request

from config import (
    API_BACKOFF_BASE,
    API_MAX_RETRIES,
    API_RATE_LIMIT_RPS,
)


class RateLimitedClient:


    def __init__(self, rps: float = API_RATE_LIMIT_RPS) -> None:
        self.min_interval = 1.0 / rps if rps and rps > 0 else 0.0
        self._last_request_ts = 0.0

    def _throttle(self) -> None:
        if self.min_interval <= 0:
            return
        now = time.monotonic()
        wait = self._last_request_ts + self.min_interval - now
        if wait > 0:
            time.sleep(wait)
        self._last_request_ts = time.monotonic()

    @staticmethod
    def _backoff_from_headers(headers) -> float | None:
        retry_after = headers.get("Retry-After")
        if retry_after:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass

        reset = headers.get("X-RateLimit-Reset")
        if reset:
            try:
                return max(0.0, float(reset) - time.time())
            except ValueError:
                pass
        return None

    def get_json(self, url: str, headers: dict) -> dict | list | None:
      
        attempt = 0
        while True:
            attempt += 1
            self._throttle()

            req = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(req) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None

                if e.code in (403, 429) and attempt <= API_MAX_RETRIES:
                    delay = self._backoff_from_headers(e.headers)
                    if delay is None:
                        delay = API_BACKOFF_BASE * (2 ** (attempt - 1))
                    # Cap so a bogus header cannot freeze the script forever
                    delay = min(delay, 300.0)
                    print(f"   rate-limited (HTTP {e.code}), sleeping {delay:.1f}s...")
                    time.sleep(delay)
                    continue

                raise
