"""Portable command line interface for pglow."""

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path

from ._version import __version__
from .config import config_path, ensure_config, load_config
from .renderer import render, terminal_width
from .source import README_NAMES, discover_markdown, from_argument
from .tui import run, view


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        prog="pglow", description="Render Markdown in a terminal."
    )
    result.add_argument(
        "source", nargs="?", help="file, directory, URL, repository, or - for stdin"
    )
    result.add_argument("-p", "--pager", action="store_true", help="display with $PAGER")
    result.add_argument(
        "-t", "--tui", action="store_true", help="browse a directory interactively"
    )
    result.add_argument(
        "-s",
        "--style",
        default=None,
        help="auto, dark, light, claude, github, mono, opencode, codex, vscode, or notty",
    )
    result.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        help="word wrap width; 0 uses terminal width",
    )
    result.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="include hidden files in directory mode",
    )
    result.add_argument(
        "-l",
        "--line-numbers",
        action="store_true",
        help="show line numbers in TUI mode",
    )
    result.add_argument(
        "-n",
        "--preserve-new-lines",
        action="store_true",
        help="preserve newlines in the output",
    )
    result.add_argument("--config", help="configuration file path")
    result.add_argument(
        "--version", action="version", version=f"pglow {__version__}"
    )
    return result


def _browse(directory: Path, include_hidden: bool) -> Path | None:
    files = discover_markdown(directory, include_hidden)
    if not files:
        raise ValueError(f"no Markdown files found in {directory}")
    for index, path in enumerate(files, 1):
        print(f"{index:>3} {path.relative_to(directory)}")
    if not sys.stdin.isatty():
        return next(
            (item for item in files if item.name.lower() in README_NAMES), files[0]
        )
    choice = input("select a file (Enter to quit): ").strip()
    if not choice:
        return None
    try:
        return files[int(choice) - 1]
    except (ValueError, IndexError) as error:
        raise ValueError("invalid file selection") from error


def _page(output: str) -> None:
    command = os.environ.get("PAGER")
    if not command:
        if sys.platform == "win32":
            sys.stdout.write(output)
            return
        command = "less -R"
    parts = shlex.split(command, posix=sys.platform != "win32")
    try:
        subprocess.run(parts, input=output, text=True, check=True)
    except (OSError, subprocess.CalledProcessError) as error:
        raise ValueError(f"unable to run pager: {error}") from error


def _edit_config(path: Path) -> int:
    ensure_config(path)
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL")
    if not editor:
        print(f"Configuration file: {path}")
        return 0
    try:
        subprocess.run(
            shlex.split(editor, posix=sys.platform != "win32") + [str(path)], check=True
        )
    except (OSError, subprocess.CalledProcessError) as error:
        print(f"unable to run editor: {error}", file=sys.stderr)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        config = load_config(config_path(args.config))
        style = args.style or str(config.get("style", "auto"))
        width = args.width if args.width is not None else int(config.get("width", 0))
        preserve = args.preserve_new_lines or bool(
            config.get("preserveNewLines", False)
        )
        line_numbers = args.line_numbers or bool(config.get("showLineNumbers", False))
        if not sys.stdout.isatty() and args.style is None:
            style = "notty"
        source_name = args.source if args.source is not None else "."
        directory = Path(source_name).expanduser()
        is_directory = directory.is_dir()

        if is_directory and (args.tui or (sys.stdin.isatty() and sys.stdout.isatty())):
            run(
                directory.resolve(),
                terminal_width(width),
                style,
                preserve,
                args.all or bool(config.get("all", False)),
                line_numbers,
            )
            return 0
        if args.tui:
            source = from_argument(source_name)
            candidate = Path(source.name)
            local_path = candidate if candidate.is_file() else None
            view(
                source.content,
                source.name,
                terminal_width(width),
                style,
                preserve,
                line_numbers,
                local_path,
            )
            return 0
        if is_directory:
            selected = _browse(directory, args.all or bool(config.get("all", False)))
            if selected is None:
                return 0
            source_name = str(selected)
        source = from_argument(source_name)
        output = render(
            source.content, terminal_width(width), style, preserve, sys.stdout.isatty()
        )
        if args.pager or bool(config.get("pager", False)):
            _page(output)
        else:
            sys.stdout.write(output)
    except (OSError, ValueError) as error:
        print(f"pglow: {error}", file=sys.stderr)
        return 1
    return 0
