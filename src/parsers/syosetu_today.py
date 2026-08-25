"""Parser for https://syosetu.today/ manga detail pages.

The page lists chapters in the "Chapters" section. Each chapter link is inside:

    <div class="chapter-box">
        <div class="entry">
            <h4><a href=".../chapter-58/">Title 【第58話】</a></h4>
        </div>
        ...
    </div>

The first entry is the latest chapter.
"""

from __future__ import annotations

import re
from typing import Optional

from bs4 import BeautifulSoup

from .base import BaseParser
from ..fetcher import fetch_html

CHAPTER_PATTERN = re.compile(r"第\s*(\d+(?:\.\d+)?)\s*(?:話|话)")
SLUG_PATTERN = re.compile(r"chapter[_-](\d+(?:[._-]\d+)?)", re.IGNORECASE)


class SyosetuTodayParser(BaseParser):
    """Parses a syosetu.today manga detail page."""

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        html = fetch_html(self.url)
        soup = BeautifulSoup(html, "html.parser")

        chapter_links = soup.select(".chapter-box .entry h4 a")
        if not chapter_links:
            # Try a looser selector in case the theme changes slightly.
            chapter_links = soup.select(".chapter-box a[href*='/chapter-']")
        if not chapter_links:
            return None

        link = chapter_links[0]
        href = link.get("href")
        text = link.get_text(" ", strip=True)

        chapter = self._extract_chapter(text, href)
        if chapter is None:
            return None

        return {
            "latest_chapter": chapter,
            "title": text,
            "url": href or self.url,
        }

    @staticmethod
    def _extract_chapter(text: str, href: Optional[str]) -> Optional[str]:
        match = CHAPTER_PATTERN.search(text)
        if match:
            number = match.group(1)
            # Keep the display form consistent, e.g. 第58話 / 第20.5話.
            return f"第{number}話"
        if href:
            slug_match = SLUG_PATTERN.search(href)
            if slug_match:
                number = slug_match.group(1).replace("-", ".").replace("_", ".")
                return f"第{number}話"
        return None