from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .parsers import get_parser
from .state import StateManager


class MangaMonitor:
    """Main manga monitoring class."""

    def __init__(
        self,
        manga_config: List[Dict[str, Any]],
        state_manager: StateManager,
        *,
        request_delay: float = 1.0,
    ) -> None:
        self.manga_config = manga_config
        self.state_manager = state_manager
        self.request_delay = request_delay
        self.updates_detected: List[Dict[str, str]] = []

    def run_check(self) -> List[Dict[str, str]]:
        """Run a full check on all enabled manga.

        A failure in one manga is logged and never stops the remaining items.
        """
        print(f"[INFO] Starting manga check for {len(self.manga_config)} manga...")

        for manga in self.manga_config:
            if not manga.get("enabled", True):
                print(f"[INFO] Skipping disabled manga: {manga['name']}")
                continue

            print(f"[INFO] Checking: {manga['name']}")

            parser_name = manga.get("parser", "default")
            parser = get_parser(parser_name, manga["name"], manga["url"])

            try:
                chapter_info = parser.get_latest_chapter()

                if chapter_info is None:
                    print(
                        f"[ERROR] {manga['name']} → Could not parse latest chapter "
                        "(page may have changed or has no chapter list)"
                    )
                    continue

                current_chapter = chapter_info["latest_chapter"]
                chapter_url = chapter_info["url"]

                print(f"[SUCCESS] {manga['name']} → {current_chapter}")

                has_updated, previous_chapter = self.state_manager.has_updated(
                    manga["name"],
                    current_chapter,
                )

                if has_updated and previous_chapter is not None:
                    print(
                        f"[UPDATED] {manga['name']} → {previous_chapter} → {current_chapter}"
                    )
                    self.updates_detected.append(
                        {
                            "name": manga["name"],
                            "chapter": current_chapter,
                            "url": chapter_url,
                            "previous": previous_chapter,
                            "current": current_chapter,
                        }
                    )
                elif previous_chapter is None:
                    print(
                        f"[INFO] {manga['name']} → first run, baseline recorded "
                        f"({current_chapter}); no notification will be sent"
                    )

                # Update state regardless so last_checked is always fresh.
                self.state_manager.update_manga(
                    manga["name"],
                    current_chapter,
                    manga["url"],
                )

                # Small delay to be respectful to the server.
                time.sleep(self.request_delay)

            except Exception as exc:
                print(f"[ERROR] {manga['name']} → {exc}")

        print(
            f"[INFO] Manga check completed. Updates detected: {len(self.updates_detected)}"
        )
        return self.updates_detected

    def get_updates(self) -> List[Dict[str, str]]:
        """Return the list of detected updates."""
        return self.updates_detected