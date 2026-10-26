"""Interactive terminal user interface for browsing and viewing Markdown."""

import os
import shutil
import sys
from pathlib import Path

from .keys import KeyReader
from .renderer import render
from .source import _remove_frontmatter, discover_markdown
from .terminal import paint_line
from .theme import Theme, load_theme


def _draw(
    lines: list[str],
    title: str,
    theme: Theme,
    offset: int = 0,
    help_text: str = "j/k or arrows: move  Enter: open",
) -> None:
    size = shutil.get_terminal_size(fallback=(80, 24))
    columns, rows = size.columns, size.lines
    page = max(rows - 2, 1)
    visible = lines[offset:offset + page]
    out = ["\033[H"]
    out.append(paint_line(" " + title, columns, theme))
    for line in visible:
        out.append(paint_line(" " + line, columns, theme))
    for _ in range(page - len(visible)):
        out.append(paint_line("", columns, theme))
    out.append(paint_line(" " + help_text, columns, theme))
    sys.stdout.write("\n".join(out))
    sys.stdout.flush()


def _load_local_document(path: Path) -> tuple[str, int]:
    content = path.read_text(encoding="utf-8", errors="replace")
    return _remove_frontmatter(content), path.stat().st_mtime_ns


def _view(
    content: str,
    name: str,
    width: int,
    style: str,
    theme: Theme,
    preserve_newlines: bool,
    line_numbers: bool,
    reader: KeyReader,
    source_path: Path | None = None,
) -> None:
    lines = render(content, width, style, preserve_newlines, colour=True).splitlines()
    modification_time = source_path.stat().st_mtime_ns if source_path else None
    offset = 0
    status = ""
    dirty = True
    last_size: os.terminal_size | None = None
    query = ""
    reverse_search = False
    while True:
        size = shutil.get_terminal_size(fallback=(80, 24))
        rows = size.lines
        if size != last_size:
            dirty = True
            last_size = size
        display_lines = (
            [f"{index:>5} {line}" for index, line in enumerate(lines, 1)]
            if line_numbers
            else lines
        )
        title = f"{name} {status}".rstrip()
        if dirty:
            _draw(
                display_lines,
                title,
                theme,
                offset,
                "/?: search  n/N: next/prev  r: reload  l: numbers  q: back",
            )
            dirty = False
        key = reader.read(timeout=0.5)
        page = max(rows - 3, 1)
        if source_path and (key == "r" or key is None):
            try:
                reloaded_content, current_time = _load_local_document(source_path)
                if key == "r" or current_time != modification_time:
                    lines = render(
                        reloaded_content, width, style, preserve_newlines, colour=True
                    ).splitlines()
                    modification_time = current_time
                    offset = min(offset, max(len(lines) - page, 0))
                    status = "(reloaded)"
                    dirty = True
                continue
            except OSError as error:
                status = f"(reload failed: {error})"
                dirty = True
                continue
        if key is None:
            continue
        if key in ("q", "quit", "esc"):
            return
        if key in ("/", "?"):
            reverse_search = key == "?"
            result = _read_search(
                reader, theme, "Search backward" if reverse_search else "Search"
            )
            if result is not None:
                query = result
                match = _search_line(
                    lines, query, offset - 1 if reverse_search else offset + 1, reverse_search
                )
                if match is None:
                    status = f"(no match: {query})"
                else:
                    offset = match
                    status = f"(match: {query})"
                dirty = True
            continue
        if key in ("n", "N") and query:
            direction = reverse_search if key == "n" else not reverse_search
            match = _search_line(
                lines, query, offset - 1 if direction else offset + 1, direction
            )
            if match is None:
                status = f"(no match: {query})"
            else:
                offset = match
                status = f"(match: {query})"
            dirty = True
            continue
        if key in ("j", "down"):
            offset = min(offset + 1, max(len(lines) - page, 0))
            dirty = True
        elif key in ("k", "up"):
            offset = max(offset - 1, 0)
            dirty = True
        elif key in (" ", "f", "pagedown"):
            offset = min(offset + page, max(len(lines) - page, 0))
            dirty = True
        elif key in ("b", "pageup"):
            offset = max(offset - page, 0)
            dirty = True
        elif key == "l":
            line_numbers = not line_numbers
            dirty = True


def view(
    content: str,
    name: str,
    width: int,
    style: str,
    preserve_newlines: bool,
    line_numbers: bool = False,
    source_path: Path | None = None,
) -> None:
    """Open one document in the interactive viewer."""
    with KeyReader() as reader:
        _view(
            content,
            name,
            width,
            style,
            load_theme(style),
            preserve_newlines,
            line_numbers,
            reader,
            source_path,
        )


def _read_search(reader: KeyReader, theme: Theme, prompt: str = "Search") -> str | None:
    """Read a search query while retaining keyboard-only TUI operation."""
    query = ""
    while True:
        rows = shutil.get_terminal_size(fallback=(80, 24)).lines
        sys.stdout.write(
            f"\033[{rows};1H\033[2K{theme.base}\033[?25h{prompt}: {query}\033[0m"
        )
        sys.stdout.flush()
        key = reader.read()
        if key == "enter":
            sys.stdout.write("\033[?25l")
            return query
        if key == "quit":
            sys.stdout.write("\033[?25l")
            return None
        if key in ("\x7f", "\b"):
            query = query[:-1]
        elif len(key) == 1 and key.isprintable():
            query += key


def _search_line(
    lines: list[str], query: str, start: int, reverse: bool
) -> int | None:
    """Find a rendered line, wrapping around the document when necessary."""
    if not query or not lines:
        return None
    needle = query.casefold()
    if reverse:
        start = max(-1, min(start, len(lines) - 1))
        indexes = range(start, -1, -1)
        wrapped = range(len(lines) - 1, start, -1)
    else:
        start = max(0, min(start, len(lines) - 1))
        indexes = range(start, len(lines))
        wrapped = range(0, start)
    for index in indexes:
        if needle in lines[index].casefold():
            return index
    for index in wrapped:
        if needle in lines[index].casefold():
            return index
    return None


def run(
    directory: Path,
    width: int,
    style: str,
    preserve_newlines: bool,
    include_hidden: bool,
    line_numbers: bool = False,
) -> None:
    """Browse Markdown files and view their rendered contents interactively."""
    files = discover_markdown(directory, include_hidden)
    if not files:
        raise ValueError(f"no Markdown files found in {directory}")
    selected = 0
    offset = 0
    query = ""
    theme = load_theme(style)
    with KeyReader() as reader:
        while True:
            rows = shutil.get_terminal_size(fallback=(80, 24)).lines
            page = max(rows - 2, 1)
            matches = [
                path
                for path in files
                if query.casefold() in str(path.relative_to(directory)).casefold()
            ]
            selected = min(selected, max(len(matches) - 1, 0))
            items = [
                f"{'›' if index == selected else ' '} {path.relative_to(directory)}"
                for index, path in enumerate(matches)
            ]
            title = f"pglow: {directory}" + (f" filter: {query}" if query else "")
            _draw(
                items or [" No matching files"],
                title,
                theme,
                offset,
                "/ or ?: filter  j/k: move  f/b: page  Enter: open",
            )
            key = reader.read()
            if key in ("q", "quit"):
                return
            if key in ("/", "?"):
                result = _read_search(reader, theme, "Filter")
                if result is not None:
                    query = result
                    selected = 0
                    offset = 0
                continue
            if key in ("j", "down") and matches:
                selected = min(selected + 1, len(matches) - 1)
            elif key in ("k", "up"):
                selected = max(selected - 1, 0)
            elif key in ("f", "pagedown"):
                selected = min(selected + page, len(matches) - 1)
            elif key in ("b", "pageup"):
                selected = max(selected - page, 0)
            elif key == "enter" and matches:
                path = matches[selected]
                content = _remove_frontmatter(
                    path.read_text(encoding="utf-8", errors="replace")
                )
                _view(
                    content,
                    path.name,
                    width,
                    style,
                    theme,
                    preserve_newlines,
                    line_numbers,
                    reader,
                    path,
                )
                continue
            if selected >= offset + page:
                offset = selected - page + 1
            elif selected < offset:
                offset = selected
