"""ANSI-aware width measurement and terminal painting."""

import re
import sys
import unicodedata

from .theme import Theme

RESET = "\033[0m"
ANSI_ESCAPE = re.compile(r"\x1b\[[0-?]*[-/]*[@-~]")


def display_width(text: str) -> int:
    """Measure terminal cells while ignoring ANSI control sequences."""
    plain = ANSI_ESCAPE.sub("", text)
    return sum(
        0
        if unicodedata.combining(character)
        else 2
        if unicodedata.east_asian_width(character) in {"W", "F"}
        else 1
        for character in plain
    )


def _truncate_ansi(text: str, width: int) -> str:
    """Trim a colored line without cutting an ANSI control sequence."""
    result: list[str] = []
    cells = 0
    position = 0
    for match in ANSI_ESCAPE.finditer(text):
        segment = text[position:match.start()]
        for character in segment:
            character_width = (
                0
                if unicodedata.combining(character)
                else 2
                if unicodedata.east_asian_width(character) in {"W", "F"}
                else 1
            )
            if cells + character_width > width:
                return "".join(result)
            result.append(character)
            cells += character_width
        result.append(match.group())
        position = match.end()
    for character in text[position:]:
        character_width = (
            0
            if unicodedata.combining(character)
            else 2
            if unicodedata.east_asian_width(character) in {"W", "F"}
            else 1
        )
        if cells + character_width > width:
            break
        result.append(character)
        cells += character_width
    return "".join(result)


def paint_line(line: str, columns: int, theme: Theme) -> str:
    """Apply a full-width themed canvas behind an ANSI-formatted line."""
    line = line.replace("\033[0m", f"\033[0m{theme.base}")
    line = _truncate_ansi(line, columns)
    padding = " " * max(columns - display_width(line), 0)
    return theme.base + line + padding + RESET


def enable_windows_ansi() -> None:
    """Enable ANSI output in modern Windows Console hosts when available."""
    if sys.platform != "win32":
        return
    try:
        import ctypes

        handle = ctypes.windll.kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        pass
