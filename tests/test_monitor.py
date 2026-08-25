"""Tests for the monitor's per-manga isolation and update detection."""

from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.monitor import MangaMonitor
from src.state import StateManager


def _state(tmp_name: str) -> StateManager:
    return StateManager(state_file=tmp_name)


class BaseMonitorTest(unittest.TestCase):
    def setUp(self) -> None:
        fd, self.state_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)

    def tearDown(self) -> None:
        if os.path.exists(self.state_path):
            os.unlink(self.state_path)


class TestFirstRun(BaseMonitorTest):
    def test_first_run_records_baseline_without_notification(self) -> None:
        state = _state(self.state_path)
        parser = Mock()
        parser.get_latest_chapter.return_value = {
            "latest_chapter": "第120話",
            "title": "Manga 第120話",
            "url": "https://syosetu.today/manga/x/chapter-120/",
        }

        config = [{"name": "Manga", "url": "https://syosetu.today/manga/x/", "parser": "syosetu_today", "enabled": True}]
        with patch("src.monitor.get_parser", return_value=parser):
            monitor = MangaMonitor(config, state, request_delay=0)
            updates = monitor.run_check()

        self.assertEqual(updates, [])
        self.assertEqual(state.get_latest_chapter("Manga"), "第120話")


class TestNoUpdate(BaseMonitorTest):
    def test_same_chapter_does_not_trigger_update(self) -> None:
        state = _state(self.state_path)
        state.update_manga("Manga", "第120話", "https://syosetu.today/manga/x/")
        parser = Mock()
        parser.get_latest_chapter.return_value = {
            "latest_chapter": "第120話",
            "title": "Manga 第120話",
            "url": "https://syosetu.today/manga/x/chapter-120/",
        }

        config = [{"name": "Manga", "url": "https://syosetu.today/manga/x/", "parser": "syosetu_today", "enabled": True}]
        with patch("src.monitor.get_parser", return_value=parser):
            monitor = MangaMonitor(config, state, request_delay=0)
            updates = monitor.run_check()

        self.assertEqual(updates, [])


class TestNewChapter(BaseMonitorTest):
    def test_new_chapter_detected(self) -> None:
        state = _state(self.state_path)
        state.update_manga("Manga", "第120話", "https://syosetu.today/manga/x/")
        parser = Mock()
        parser.get_latest_chapter.return_value = {
            "latest_chapter": "第121話",
            "title": "Manga 第121話",
            "url": "https://syosetu.today/manga/x/chapter-121/",
        }

        config = [{"name": "Manga", "url": "https://syosetu.today/manga/x/", "parser": "syosetu_today", "enabled": True}]
        with patch("src.monitor.get_parser", return_value=parser):
            monitor = MangaMonitor(config, state, request_delay=0)
            updates = monitor.run_check()

        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["previous"], "第120話")
        self.assertEqual(updates[0]["current"], "第121話")
        self.assertEqual(state.get_latest_chapter("Manga"), "第121話")


class TestFailureIsolation(BaseMonitorTest):
    def test_one_failure_does_not_stop_others(self) -> None:
        state = _state(self.state_path)

        def parser_factory(_parser_name: str, name: str, _url: str) -> Mock:
            parser = Mock()
            if name == "Bad":
                parser.get_latest_chapter.side_effect = RuntimeError("boom")
            else:
                parser.get_latest_chapter.return_value = {
                    "latest_chapter": "第10話",
                    "title": "Good 第10話",
                    "url": "https://syosetu.today/manga/good/chapter-10/",
                }
            return parser

        config = [
            {"name": "Bad", "url": "https://syosetu.today/manga/bad/", "parser": "syosetu_today", "enabled": True},
            {"name": "Good", "url": "https://syosetu.today/manga/good/", "parser": "syosetu_today", "enabled": True},
        ]
        with patch("src.monitor.get_parser", side_effect=parser_factory):
            monitor = MangaMonitor(config, state, request_delay=0)
            updates = monitor.run_check()

        self.assertEqual(updates, [])
        self.assertIsNone(state.get_latest_chapter("Bad"))
        self.assertEqual(state.get_latest_chapter("Good"), "第10話")


class TestDisabled(BaseMonitorTest):
    def test_disabled_manga_skipped(self) -> None:
        state = _state(self.state_path)
        parser = Mock()

        config = [
            {"name": "Off", "url": "https://syosetu.today/manga/off/", "parser": "syosetu_today", "enabled": False}
        ]
        with patch("src.monitor.get_parser", return_value=parser) as mock_factory:
            monitor = MangaMonitor(config, state, request_delay=0)
            monitor.run_check()

        mock_factory.assert_not_called()
        self.assertIsNone(state.get_latest_chapter("Off"))


if __name__ == "__main__":
    unittest.main()