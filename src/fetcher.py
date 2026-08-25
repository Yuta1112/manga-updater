"""HTTP fetching helpers with timeout and bounded retry.

The module deliberately keeps retry count small and does not attempt to bypass
rate limits, login walls, Cloudflare challenges, or CAPTCHA protections.
"""

from __future__ import annotations

import time
from typing import Optional

import requests

DEFAULT_TIMEOUT = 20
DEFAULT_RETRIES = 3
DEFAULT_BACKOFF_SECONDS = 2.0

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


class FetchError(Exception):
    """Raised when a page cannot be fetched after bounded retries."""

    def __init__(self, message: str, status_code: Optional[int] = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _should_retry(status_code: Optional[int]) -> bool:
    # Retry on common transient failures; do not retry on permanent client errors.
    if status_code is None:  # network-level error
        return True
    return status_code in {408, 425, 429, 500, 502, 503, 504}


def fetch_html(
    url: str,
    *,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = DEFAULT_RETRIES,
    backoff: float = DEFAULT_BACKOFF_SECONDS,
    headers: Optional[dict[str, str]] = None,
) -> str:
    """Fetch a URL and return its text content.

    Raises FetchError after bounded retries. Permanent HTTP errors such as 403,
    404, and 405 are raised immediately because retrying would be pointless.
    """
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Language": "ja,en;q=0.8",
    }
    if headers:
        request_headers.update(headers)

    last_error: Optional[Exception] = None
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, headers=request_headers, timeout=timeout)
            if response.status_code == 200:
                response.encoding = response.apparent_encoding or response.encoding
                return response.text

            if not _should_retry(response.status_code):
                raise FetchError(
                    f"HTTP {response.status_code} for {url}",
                    status_code=response.status_code,
                )

            # Transient HTTP error: keep the error and retry.
            last_error = FetchError(
                f"HTTP {response.status_code} for {url}",
                status_code=response.status_code,
            )
        except requests.Timeout as exc:
            last_error = FetchError(f"Timeout for {url}: {exc}")
        except requests.RequestException as exc:
            last_error = FetchError(f"Request failed for {url}: {exc}")

        if attempt < retries:
            time.sleep(backoff * attempt)

    assert last_error is not None
    raise last_error