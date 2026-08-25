"""Tests for PushPlus notification logic."""

from __future__ import annotations

import os
import unittest
from unittest.mock import Mock, patch

from src.notifier import PushPlusNotifier


class TestPushPlusNotifier(unittest.TestCase):
    def test_token_missing_raises_clear_error(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as ctx:
                PushPlusNotifier(token=None)

        self.assertIn("PUSHPLUS_TOKEN is not configured", str(ctx.exception))

    def test_send_notification_merges_updates_into_one_message(self) -> None:
        notifier = PushPlusNotifier(token="test-token")
        updates = [
            {"name": "MangaA", "chapter": "第121話", "url": "https://a/121"},
            {"name": "MangaB", "chapter": "第56話", "url": "https://b/56"},
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 200, "msg": "success"}

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            ok = notifier.send_notification(updates)

        self.assertTrue(ok)
        self.assertEqual(mock_post.call_count, 1)
        payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(payload["token"], "test-token")
        self.assertIn("MangaA", payload["content"])
        self.assertIn("第121話", payload["content"])
        self.assertIn("MangaB", payload["content"])
        self.assertIn("第56話", payload["content"])

    def test_no_updates_skips_request(self) -> None:
        notifier = PushPlusNotifier(token="test-token")

        with patch("src.notifier.requests.post") as mock_post:
            ok = notifier.send_notification([])

        self.assertTrue(ok)
        mock_post.assert_not_called()

    def test_send_notification_fails_returns_false(self) -> None:
        notifier = PushPlusNotifier(token="test-token")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 400, "msg": "bad token"}

        with patch("src.notifier.requests.post", return_value=mock_response):
            ok = notifier.send_notification(
                [{"name": "Manga", "chapter": "第1話", "url": "https://a/1"}]
            )

        self.assertFalse(ok)

    def test_test_connection(self) -> None:
        notifier = PushPlusNotifier(token="test-token")
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"code": 200, "msg": "success"}

        with patch("src.notifier.requests.post", return_value=mock_response) as mock_post:
            ok = notifier.test_connection()

        self.assertTrue(ok)
        self.assertEqual(mock_post.call_count, 1)
        payload = mock_post.call_args.kwargs["json"]
        self.assertIn("PushPlus", payload["title"])


if __name__ == "__main__":
    unittest.main()