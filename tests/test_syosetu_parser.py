"""Tests for the syosetu.today parser."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from src.parsers.syosetu_today import SyosetuTodayParser

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="ja">
<head><meta charset="UTF-8"></head>
<body>
<div class="row gy-6">
  <div class="col-sm">
    <p class="font-bold font-15x mb-4 text-warning">Chapters</p>
    <div class="chapter-box">
      <div class="entry pt-3 border-top mb-3 pe-3">
        <div class="d-flex align-items-center mb-1 justify-content-between">
          <p class="text-muted font-9x">2026/01/01</p>
        </div>
        <h4 class="font-bold font-12x">
          <a href="https://syosetu.today/manga/example-raw-free/chapter-58/">Example (Raw – Free) 【第58話】</a>
        </h4>
      </div>
      <div class="entry pt-3 border-top mb-3 pe-3">
        <h4 class="font-bold font-12x">
          <a href="https://syosetu.today/manga/example-raw-free/chapter-57/">Example (Raw – Free) 【第57話】</a>
        </h4>
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""


class TestSyosetuTodayParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = SyosetuTodayParser(name="Test", url="https://syosetu.today/manga/example-raw-free/")

    def test_parses_latest_chapter(self) -> None:
        with patch("src.parsers.syosetu_today.fetch_html", return_value=SAMPLE_HTML):
            result = self.parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第58話")
        self.assertIn("【第58話】", result["title"])
        self.assertEqual(
            result["url"],
            "https://syosetu.today/manga/example-raw-free/chapter-58/",
        )

    def test_decimal_chapter_from_text(self) -> None:
        html = SAMPLE_HTML.replace("第58話", "第20.5話").replace(
            "chapter-58", "chapter-20-5"
        )
        with patch("src.parsers.syosetu_today.fetch_html", return_value=html):
            result = self.parser.get_latest_chapter()

        self.assertIsNotNone(result)
        self.assertEqual(result["latest_chapter"], "第20.5話")

    def test_returns_none_when_no_chapters(self) -> None:
        empty_html = "<html><body><div class='chapter-box'></div></body></html>"
        with patch("src.parsers.syosetu_today.fetch_html", return_value=empty_html):
            result = self.parser.get_latest_chapter()

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()