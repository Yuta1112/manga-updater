"""Parser for https://mangadex.org/ title pages.

MangaDex is a single-page app: the HTML shell is a few kilobytes and contains
no chapter data, so scraping the page cannot work. The public API is stable and
needs no credentials:

    GET https://api.mangadex.org/manga/{uuid}/feed
        ?limit=100&order[chapter]=desc&includeExternalUrl=0

Chapter numbers are returned as strings and may be empty, decimal, or repeated
across languages, so the parser takes the highest numeric value it sees.
"""

from __future__ import annotations

import re
from typing import Any, Optional

from .base import BaseParser
from ..chapter import normalize_chapter_number
from ..fetcher import FetchError, fetch_json

TITLE_ID_PATTERN = re.compile(
    r"mangadex\.org/title/([0-9a-fA-F-]{32,36})"
)
API_TEMPLATE = (
    "https://api.mangadex.org/manga/{uuid}/feed"
    "?limit=100&order%5Bchapter%5D=desc&includeExternalUrl=0"
)


class MangaDexParser(BaseParser):
    """Parses a mangadex.org title through the official API."""

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        match = TITLE_ID_PATTERN.search(self.url)
        if not match:
            return None

        api_url = API_TEMPLATE.format(uuid=match.group(1))
        try:
            payload: Any = fetch_json(api_url)
        except FetchError:
            return None

        if not isinstance(payload, dict):
            return None

        best: Optional[tuple[float, str, str]] = None
        for entry in payload.get("data") or []:
            attributes = entry.get("attributes") or {}
            raw = attributes.get("chapter")
            if not raw:
                continue
            number = normalize_chapter_number(str(raw))
            if number is None:
                continue
            chapter_id = entry.get("id")
            if best is None or number > best[0]:
                display = str(raw).strip()
                best = (number, f"第{display}話", chapter_id or "")

        if best is None:
            return None

        _, chapter, chapter_id = best
        url = f"https://mangadex.org/chapter/{chapter_id}" if chapter_id else self.url
        return {"latest_chapter": chapter, "title": chapter, "url": url}
