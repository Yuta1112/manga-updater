"""Generic fallback parser for manga sites without a dedicated parser.

The original implementation stopped at the first chapter-like element it found,
which meant a page listing ``第1話 … 第17話`` was always reported as ``第1話``
and could never signal an update. It also used jQuery-style ``:contains()``
selectors that newer versions of soupsieve reject outright.

This version walks a ladder of progressively looser selectors and, within the
first selector that matches anything, keeps the **highest** chapter number. That
avoids both failure modes while staying site-agnostic.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseParser
from ..fetcher import FetchError, fetch_html

CHAPTER_PATTERN = re.compile(
    r"(?:第\s*(\d+(?:\.\d+)?)\s*[話话]|[Cc]hapter\s*(\d+(?:\.\d+)?))"
)

# Tried in order; the first selector that yields a chapter number wins. Narrow
# list selectors come first so a "you may also like" sidebar cannot outvote the
# real chapter table.
SELECTOR_LADDER = (
    ".chapters .chapter a",
    ".chapters a",
    "#chapter-list a",
    ".chapter-list a",
    ".episode-list a",
    ".episodes a",
    "table.uk-table a",
    "[class*='chapter'] a",
    ".chapter a",
    "[class*='episode'] a",
    "a[href*='chapter']",
    "a[href*='episode']",
)


class DefaultParser(BaseParser):
    """Best-effort parser for common manga sites."""

    def __init__(self, name: str, url: str):
        super().__init__(name, url)

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        try:
            html = fetch_html(self.url)
        except FetchError as exc:
            print(f"[ERROR] Failed to fetch {self.name}: {exc.message}")
            return None

        soup = BeautifulSoup(html, "html.parser")

        for selector in SELECTOR_LADDER:
            try:
                elements = soup.select(selector)
            except Exception:  # unsupported selector, try the next one
                continue
            result = self._scan(elements)
            if result is not None:
                return result

        print(f"[WARN] Could not parse latest chapter for {self.name}")
        return None

    def _scan(self, elements) -> Optional[dict[str, str]]:
        """Return the highest-numbered chapter among ``elements``."""
        best: Optional[tuple[float, str, str]] = None

        for element in elements:
            text = element.get_text(" ", strip=True)
            match = CHAPTER_PATTERN.search(text)
            if not match:
                continue

            raw = match.group(1) or match.group(2)
            try:
                number = float(raw)
            except ValueError:
                continue

            if best is not None and number <= best[0]:
                continue

            href = element.get("href")
            url = urljoin(self.url, href) if href else self.url
            best = (number, text[:200], url)

        if best is None:
            return None

        number, title, url = best
        return {"latest_chapter": f"第{number:g}話", "title": title, "url": url}
