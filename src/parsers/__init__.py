"""Parser registry.

Each manga config's ``parser`` field selects an entry here. Add new parsers by
implementing :class:`BaseParser` and registering the class in ``PARSER_REGISTRY``.
"""

from __future__ import annotations

from typing import Type

from .base import BaseParser
from .default_parser import DefaultParser
from .ganma import GanmaParser
from .jump_plus import JumpPlusParser
from .manga_up import MangaUpParser
from .mangadex import MangaDexParser
from .syosetu_today import SyosetuTodayParser

PARSER_REGISTRY: dict[str, Type[BaseParser]] = {
    "default": DefaultParser,
    "syosetu_today": SyosetuTodayParser,
    "ganma": GanmaParser,
    "manga_up": MangaUpParser,
    "jump_plus": JumpPlusParser,
    "mangadex": MangaDexParser,
}


def get_parser(parser_name: str, name: str, url: str) -> BaseParser:
    """Return a parser instance for the given parser name.

    Unknown parser names fall back to ``DefaultParser`` so one misconfigured
    entry cannot stop the whole monitor.
    """
    parser_cls = PARSER_REGISTRY.get(parser_name, DefaultParser)
    return parser_cls(name=name, url=url)


__all__ = [
    "BaseParser",
    "DefaultParser",
    "GanmaParser",
    "JumpPlusParser",
    "MangaUpParser",
    "MangaDexParser",
    "SyosetuTodayParser",
    "PARSER_REGISTRY",
    "get_parser",
]
