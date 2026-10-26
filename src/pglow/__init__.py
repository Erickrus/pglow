"""pglow: a cross-platform terminal Markdown reader."""

from ._version import __version__
from .cli import main
from .renderer import render
from .theme import THEMES, Theme, load_theme
from .tui import run, view

__all__ = [
    "__version__",
    "main",
    "render",
    "run",
    "view",
    "Theme",
    "THEMES",
    "load_theme",
]
