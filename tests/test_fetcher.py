"""Tests for the bounded-retry HTTP fetcher."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

import requests

from src.fetcher import FetchError, fetch_html


def _ok_response(text: str) -> Mock:
    resp = Mock()
    resp.status_code = 200
    resp.text = text
    resp.apparent_encoding = "utf-8"
    resp.encoding = "utf-8"
    return resp


class TestFetchHtml(unittest.TestCase):
    def test_success_returns_text(self) -> None:
        with patch("src.fetcher.requests.get") as mock_get:
            mock_get.return_value = _ok_response("<html>ok</html>")

            result = fetch_html("https://example.com/")

        self.assertEqual(result, "<html>ok</html>")
        mock_get.assert_called_once()

    def test_retries_on_500_then_succeeds(self) -> None:
        responses = [
            Mock(status_code=500),
            Mock(status_code=500),
            _ok_response("<html>ok</html>"),
        ]

        with patch("src.fetcher.requests.get", side_effect=responses), \
             patch("src.fetcher.time.sleep") as mock_sleep:
            result = fetch_html("https://example.com/", retries=3, backoff=0)

        self.assertEqual(result, "<html>ok</html>")
        self.assertEqual(mock_sleep.call_count, 2)

    def test_raises_on_permanent_404(self) -> None:
        with patch("src.fetcher.requests.get") as mock_get:
            mock_get.return_value = Mock(status_code=404, text="not found")

            with self.assertRaises(FetchError) as ctx:
                fetch_html("https://example.com/", retries=3, backoff=0)

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(mock_get.call_count, 1)

    def test_raises_after_retries_on_timeout(self) -> None:
        with patch("src.fetcher.requests.get", side_effect=requests.Timeout("boom")), \
             patch("src.fetcher.time.sleep"):
            with self.assertRaises(FetchError):
                fetch_html("https://example.com/", retries=3, backoff=0)


if __name__ == "__main__":
    unittest.main()