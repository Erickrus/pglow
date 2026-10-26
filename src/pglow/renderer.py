"""A conservative ANSI Markdown renderer using only the standard library."""

import re
import shutil
import textwrap

from .terminal import RESET
from .theme import load_theme

INLINE_CODE = re.compile(r"`([^`]+)`")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)(?: [^)]+)?\)")


def terminal_width(requested: int) -> int:
    if requested:
        return requested
    return min(shutil.get_terminal_size(fallback=(80, 24)).columns, 120)


def _inline(text: str, colour: bool, code_style: str) -> str:
    text = LINK.sub(lambda match: f"{match.group(1)} ({match.group(2)})", text)
    text = INLINE_CODE.sub(
        lambda match: f"{code_style}{match.group(1)}{RESET}" if colour else match.group(1),
        text,
    )
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*(.+?)\*(?!\*)", r"\1", text)
    return text


def render(
    markdown: str,
    width: int = 0,
    style: str = "auto",
    preserve_newlines: bool = False,
    colour: bool = True,
) -> str:
    """Render common Markdown constructs into readable terminal text."""
    width = terminal_width(width)
    if style == "notty":
        colour = False
    theme = load_theme(style)
    output: list[str] = []
    in_code = False
    code_language = ""
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            text = _inline(" ".join(paragraph), colour, theme.code_style)
            output.extend(textwrap.wrap(text, width))
            paragraph = []

    for line in markdown.splitlines():
        if line.startswith("```"):
            if not in_code:
                code_language = line[3:].strip()
                if code_language:
                    output.append(f"[{code_language}]")
            in_code = not in_code
            continue
        if in_code:
            output.append(f"  {line}")
            continue
        if not line:
            flush_paragraph()
            if preserve_newlines or (output and output[-1] != ""):
                output.append("")
            continue
        if heading := re.match(r"^(#{1,6})\s+(.+?)\s*$", line):
            flush_paragraph()
            title = _inline(heading.group(2), colour, theme.code_style)
            output.append(f"{theme.heading}{title}{RESET}" if colour else title)
            continue
        if re.match(r"^\s*([-*_])(?:\s*\1){2,}\s*$", line):
            flush_paragraph()
            output.append("-" * min(width, 40))
            continue
        if match := re.match(r"(\s*)([-+*]|\d+\.)\s+(.+)$", line):
            flush_paragraph()
            indent = " " * len(match.group(1))
            prefix = indent + match.group(2) + " "
            output.extend(
                textwrap.wrap(
                    _inline(match.group(3), colour, theme.code_style),
                    width,
                    initial_indent=prefix,
                    subsequent_indent=" " * len(prefix),
                )
            )
            continue
        if line.startswith(">"):
            flush_paragraph()
            output.extend(
                textwrap.wrap(
                    _inline(line.lstrip("> "), colour, theme.code_style),
                    width - 2,
                    initial_indent="> ",
                    subsequent_indent="> ",
                )
            )
            continue
        if line.startswith("|") and line.endswith("|"):
            flush_paragraph()
            if not re.fullmatch(r"[|:\- ]+", line):
                output.append(
                    " | ".join(part.strip() for part in line.strip("|").split("|"))
                )
            continue
        paragraph.append(line)

    flush_paragraph()
    return "\n".join(output)
