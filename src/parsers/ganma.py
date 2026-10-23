"""Parser for https://ganma.jp/ magazine pages.

Ganma pages are a Next.js app. Chapter rows are plain links:

    <a class="flex w-full items-center ..." href="/web/reader/amakishi/<uuid>/0">
        2026/04/19 配信 第1話
    </a>

The web edition only publishes the free chapters (usually the first few); the
rest live in the mobile app. This parser therefore reports the newest chapter
that is actually readable on the web, which is what the site itself exposes.

An ``upcoming`` entry in the embedded JSON may advertise a chapter that has not
been released yet. It is deliberately ignored so the monitor does not announce
a chapter before readers can open it.
"""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseParser
from ..chapter import normalize_chapter_number
from ..fetcher import fetch_html

CHAPTER_PATTERN = re.compile(r"第\s*(\d+(?:\.\d+)?)\s*話")
READER_LINK_SELECTOR = 'a[href*="/web/reader/"]'


class GanmaParser(BaseParser):
    """Parses a ganma.jp magazine page."""

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        html = fetch_html(self.url)
        soup = BeautifulSoup(html, "html.parser")

        latest: Optional[tuple[float, str, str]] = None

        for link in soup.select(READER_LINK_SELECTOR):
            text = link.get_text(" ", strip=True)
            match = CHAPTER_PATTERN.search(text)
            if not match:
                continue
            number = float(match.group(1))
            href = urljoin(self.url, link.get("href", ""))
            if latest is None or number > latest[0]:
                latest = (number, f"第{match.group(1)}話", href)

        if latest is None:
            # Fall back to any "第N話" text on the page (e.g. layout change).
            numbers = CHAPTER_PATTERN.findall(soup.get_text(" ", strip=True))
            if not numbers:
                return None
            best = max(numbers, key=lambda n: normalize_chapter_number(n) or -1.0)
            return {"latest_chapter": f"第{best}話", "title": f"第{best}話", "url": self.url}

        _, chapter, href = latest
        return {"latest_chapter": chapter, "title": chapter, "url": href}
