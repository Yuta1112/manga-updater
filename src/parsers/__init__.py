"""Parser registry.

Each manga config's ``parser`` field selects an entry here. Add new parsers by
implementing :class:`BaseParser` and registering the class in ``PARSER_REGISTRY``.
"""

from __future__ import annotations

from typing import Type

from .base import BaseParser
from .default_parser import DefaultParser
from .syosetu_today import SyosetuTodayParser

PARSER_REGISTRY: dict[str, Type[BaseParser]] = {
    "default": DefaultParser,
    "syosetu_today": SyosetuTodayParser,
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
    "SyosetuTodayParser",
    "PARSER_REGISTRY",
    "get_parser",
]