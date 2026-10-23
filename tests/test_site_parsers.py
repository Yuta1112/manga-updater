"""Tests for the site-specific parsers (ganma, manga-up, jump+, mangadex)
and for the rewritten default parser's "highest chapter wins" behaviour.
"""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.parsers.default_parser import DefaultParser
from src.parsers.ganma import GanmaParser
from src.parsers.jump_plus import JumpPlusParser
from src.parsers.manga_up import MangaUpParser
from src.parsers.mangadex import MangaDexParser

# ---------------------------------------------------------------- fixtures

GANMA_HTML = """
<html><body>
<a href="/web/reader/amakishi/aaa/0">2026/04/19 配信 第1話</a>
<a href="/web/reader/amakishi/bbb/0">2026/05/03 配信 第3話</a>
<a href="/web/reader/amakishi/ccc/0">2026/05/31 配信 第5話</a>
<a href="/web/reader/amakishi/ddd/0">2026/05/17 配信 第4話</a>
<p>全 16 話をアプリで見る</p>
</body></html>
"""

MANGA_UP_HTML = (
    '<html><script>self.__next_f.push([1,"{\\"chapters\\":['
    '{\\"id\\":309538,\\"name\\":\\"第1話\\",\\"subName\\":\\"\\"},'
    '{\\"id\\":348777,\\"name\\":\\"第21話 - ①\\",\\"subName\\":\\"\\"},'
    '{\\"id\\":348780,\\"name\\":\\"第21話 - ②\\",\\"subName\\":\\"\\"},'
    '{\\"id\\":309541,\\"name\\":\\"第2話\\",\\"subName\\":\\"\\"}'
    ']} "])</script></html>'
)

JUMP_EPISODE_HTML = """
<html><head>
<link rel="alternate" type="application/rss+xml"
      href="https://shonenjumpplus.com/rss/series/3270375685467153822?free_only=1">
<link rel="alternate" type="application/rss+xml"
      href="https://shonenjumpplus.com/rss/series/3270375685467153822">
</head><body><h1>[1話]クラスメイド</h1></body></html>
"""

JUMP_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel>
  <title>少年ジャンプ＋（クラスメイド）</title>
  <item><title>[5話]クラスメイド</title><link>https://shonenjumpplus.com/episode/5</link></item>
  <item><title>[4話]クラスメイド</title><link>https://shonenjumpplus.com/episode/4</link></item>
  <item><title>[3話]クラスメイド</title><link>https://shonenjumpplus.com/episode/3</link></item>
</channel></rss>
"""

MANGADEX_PAYLOAD = {
    "result": "ok",
    "data": [
        {"id": "ch-45", "attributes": {"chapter": "45", "translatedLanguage": "en"}},
        {"id": "ch-9", "attributes": {"chapter": "9", "translatedLanguage": "en"}},
        {"id": "ch-none", "attributes": {"chapter": None, "translatedLanguage": "en"}},
        {"id": "ch-44", "attributes": {"chapter": "44", "translatedLanguage": "ja"}},
    ],
}

DEFAULT_HTML = """
<html><body>
<div class="chapters">
  <div class="chapter"><a href="/c/1">第1話</a></div>
  <div class="chapter"><a href="/c/17">第17話</a></div>
  <div class="chapter"><a href="/c/9">第9話</a></div>
</div>
<div class="widget"><div class="chapter"><a href="/other/78.5">Chapter 78.5</a></div></div>
</body></html>
"""


class TestGanmaParser(unittest.TestCase):
    def test_picks_highest_chapter_link(self) -> None:
        parser = GanmaParser(name="T", url="https://ganma.jp/web/magazine/amakishi")
        with patch("src.parsers.ganma.fetch_html", return_value=GANMA_HTML):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第5話")
        self.assertEqual(result["url"], "https://ganma.jp/web/reader/amakishi/ccc/0")

    def test_returns_none_without_chapters(self) -> None:
        parser = GanmaParser(name="T", url="https://ganma.jp/web/magazine/x")
        with patch("src.parsers.ganma.fetch_html", return_value="<html></html>"):
            self.assertIsNone(parser.get_latest_chapter())


class TestMangaUpParser(unittest.TestCase):
    def test_picks_highest_and_builds_chapter_url(self) -> None:
        parser = MangaUpParser(name="T", url="https://www.manga-up.com/titles/1593")
        with patch("src.parsers.manga_up.fetch_html", return_value=MANGA_UP_HTML):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第21話")
        self.assertEqual(
            result["url"], "https://www.manga-up.com/titles/1593/chapters/348777"
        )

    def test_returns_none_without_payload(self) -> None:
        parser = MangaUpParser(name="T", url="https://www.manga-up.com/titles/1")
        with patch("src.parsers.manga_up.fetch_html", return_value="<html></html>"):
            self.assertIsNone(parser.get_latest_chapter())


class TestJumpPlusParser(unittest.TestCase):
    def test_discovers_rss_from_episode_page(self) -> None:
        parser = JumpPlusParser(
            name="T", url="https://shonenjumpplus.com/episode/316112896809263395"
        )

        def fake_fetch(url, **kwargs):
            return JUMP_RSS if "/rss/series/" in url else JUMP_EPISODE_HTML

        with patch("src.parsers.jump_plus.fetch_html", side_effect=fake_fetch):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第5話")
        self.assertEqual(result["url"], "https://shonenjumpplus.com/episode/5")

    def test_prefers_unrestricted_feed(self) -> None:
        parser = JumpPlusParser(name="T", url="https://shonenjumpplus.com/episode/1")
        with patch("src.parsers.jump_plus.fetch_html", return_value=JUMP_EPISODE_HTML):
            feed = parser._resolve_feed_url()

        self.assertEqual(
            feed, "https://shonenjumpplus.com/rss/series/3270375685467153822"
        )

    def test_accepts_direct_rss_url(self) -> None:
        parser = JumpPlusParser(
            name="T", url="https://shonenjumpplus.com/rss/series/3270375685467153822"
        )
        with patch("src.parsers.jump_plus.fetch_html", return_value=JUMP_RSS):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第5話")

    def test_returns_none_without_rss_link(self) -> None:
        parser = JumpPlusParser(name="T", url="https://shonenjumpplus.com/episode/1")
        with patch("src.parsers.jump_plus.fetch_html", return_value="<html></html>"):
            self.assertIsNone(parser.get_latest_chapter())


class TestMangaDexParser(unittest.TestCase):
    def test_uses_api_and_picks_numeric_max(self) -> None:
        parser = MangaDexParser(
            name="T",
            url="https://mangadex.org/title/c4ca02fb-8378-433b-8049-fbbea5d25cba/haimiya",
        )
        with patch("src.parsers.mangadex.fetch_json", return_value=MANGADEX_PAYLOAD):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第45話")
        self.assertEqual(result["url"], "https://mangadex.org/chapter/ch-45")

    def test_returns_none_on_bad_url(self) -> None:
        parser = MangaDexParser(name="T", url="https://mangadex.org/")
        self.assertIsNone(parser.get_latest_chapter())

    def test_returns_none_on_empty_feed(self) -> None:
        parser = MangaDexParser(
            name="T", url="https://mangadex.org/title/c4ca02fb-8378-433b-8049-fbbea5d25cba/x"
        )
        with patch("src.parsers.mangadex.fetch_json", return_value={"data": []}):
            self.assertIsNone(parser.get_latest_chapter())


class TestDefaultParserMax(unittest.TestCase):
    def test_returns_highest_not_first(self) -> None:
        parser = DefaultParser(name="T", url="https://example.com/title")
        with patch("src.parsers.default_parser.fetch_html", return_value=DEFAULT_HTML):
            result = parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第17話")
        self.assertEqual(result["url"], "https://example.com/c/17")

    def test_sidebar_does_not_outvote_chapter_table(self) -> None:
        """The widget has 78.5, but it is not part of the chapter list."""
        parser = DefaultParser(name="T", url="https://example.com/title")
        with patch("src.parsers.default_parser.fetch_html", return_value=DEFAULT_HTML):
            result = parser.get_latest_chapter()

        self.assertNotEqual(result["latest_chapter"], "第78.5話")

    def test_returns_none_when_nothing_matches(self) -> None:
        parser = DefaultParser(name="T", url="https://example.com/title")
        with patch(
            "src.parsers.default_parser.fetch_html",
            return_value="<html><body>nothing</body></html>",
        ):
            self.assertIsNone(parser.get_latest_chapter())


if __name__ == "__main__":
    unittest.main()
