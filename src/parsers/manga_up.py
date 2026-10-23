"""Parser for https://www.manga-up.com/ title pages.

The page is a Next.js app that ships the whole chapter list inside the flight
payload, JSON-escaped as:

    \\"chapters\\":[{\\"id\\":309538,\\"name\\":\\"第1話\\",...}, ...]

Chapter pages are reachable at ``/titles/{title_id}/chapters/{chapter_id}``.
The list is in publication order, so the newest chapter is the one with the
highest number rather than simply the last element.
"""

from __future__ import annotations

import re
from typing import Optional

from .base import BaseParser
from ..chapter import normalize_chapter_number
from ..fetcher import fetch_html

TITLE_ID_PATTERN = re.compile(r"/titles/(\d+)")
CHAPTER_ENTRY_PATTERN = re.compile(
    r'"id":(\d+),"name":"(第\s*\d+(?:\.\d+)?\s*話[^"]*)"'
)
CHAPTER_NUMBER_PATTERN = re.compile(r"第\s*(\d+(?:\.\d+)?)\s*話")


class MangaUpParser(BaseParser):
    """Parses a manga-up.com title page."""

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        html = fetch_html(self.url)
        # The payload escapes quotes, so unescape before matching.
        payload = html.replace('\\"', '"')

        best: Optional[tuple[float, str, str]] = None
        for chapter_id, raw_name in CHAPTER_ENTRY_PATTERN.findall(payload):
            match = CHAPTER_NUMBER_PATTERN.search(raw_name)
            if not match:
                continue
            number = float(match.group(1))
            if best is None or number > best[0]:
                best = (number, f"第{match.group(1)}話", chapter_id)

        if best is None:
            return None

        number, chapter, chapter_id = best
        title_match = TITLE_ID_PATTERN.search(self.url)
        if title_match:
            url = (
                f"https://www.manga-up.com/titles/{title_match.group(1)}"
                f"/chapters/{chapter_id}"
            )
        else:
            url = self.url

        # Keep the decimal formatting consistent with the rest of the project.
        assert normalize_chapter_number(chapter) == number
        return {"latest_chapter": chapter, "title": chapter, "url": url}
