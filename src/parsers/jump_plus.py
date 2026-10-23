"""Parser for https://shonenjumpplus.com/ series, using the official RSS feed.

Every episode page carries a discovery link to the series feed:

    <link rel="alternate" type="application/rss+xml"
          href="https://shonenjumpplus.com/rss/series/3270375685467153822">

The feed lists episodes newest-first with titles such as ``[5話]クラスメイド``,
so a single small request yields the latest chapter. This avoids parsing the
JavaScript-rendered series page entirely.

A ``?free_only=1`` variant of the feed exists; the unrestricted feed is
preferred so paid/latest episodes are still counted.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from typing import Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .base import BaseParser
from ..fetcher import fetch_html

CHAPTER_PATTERN = re.compile(r"\[?\s*第?\s*(\d+(?:\.\d+)?)\s*話\s*\]?")
RSS_HREF_PATTERN = re.compile(r"/rss/series/\d+")
ATOM_HREF_PATTERN = re.compile(r"/atom/series/\d+")


class JumpPlusParser(BaseParser):
    """Parses a shonenjumpplus.com series through its RSS feed."""

    def get_latest_chapter(self) -> Optional[dict[str, str]]:
        feed_url = self._resolve_feed_url()
        if feed_url is None:
            return None

        xml_text = fetch_html(feed_url, encoding="utf-8", headers={"Accept": "application/rss+xml"})
        return self._parse_feed(xml_text)

    # ------------------------------------------------------------------ helpers

    def _resolve_feed_url(self) -> Optional[str]:
        """Return the RSS URL, discovering it from the page when necessary."""
        if RSS_HREF_PATTERN.search(self.url):
            return self.url
        if ATOM_HREF_PATTERN.search(self.url):
            return self.url.replace("/atom/series/", "/rss/series/")

        html = fetch_html(self.url)
        soup = BeautifulSoup(html, "html.parser")

        candidates = []
        for link in soup.find_all("link", rel="alternate"):
            href = link.get("href") or ""
            if not RSS_HREF_PATTERN.search(href):
                continue
            candidates.append(urljoin(self.url, href))

        if not candidates:
            # Some pages expose the feed only as a plain anchor.
            for anchor in soup.find_all("a", href=True):
                if RSS_HREF_PATTERN.search(anchor["href"]):
                    candidates.append(urljoin(self.url, anchor["href"]))

        if not candidates:
            return None

        # Prefer the unrestricted feed over the free-only one.
        candidates.sort(key=lambda u: "free_only" in u)
        return candidates[0]

    @staticmethod
    def _parse_feed(xml_text: str) -> Optional[dict[str, str]]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return None

        items = root.findall(".//item")
        if not items:
            return None

        # Feeds are newest-first, but pick the highest number to be safe.
        best: Optional[tuple[float, str, str]] = None
        for item in items:
            title = (item.findtext("title") or "").strip()
            match = CHAPTER_PATTERN.search(title)
            if not match:
                continue
            number = float(match.group(1))
            link = (item.findtext("link") or "").strip() or None
            if best is None or number > best[0]:
                best = (number, f"第{match.group(1)}話", link or "")

        if best is None:
            return None

        _, chapter, link = best
        return {"latest_chapter": chapter, "title": chapter, "url": link}
