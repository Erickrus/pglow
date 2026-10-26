"""Terminal color themes shared by the renderer and TUI."""

import re
from dataclasses import dataclass

HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def colour(value: str, background: bool = False) -> str:
    if not HEX_COLOR.fullmatch(value):
        raise ValueError(f"invalid theme color: {value!r}; use #RRGGBB")
    red, green, blue = (int(value[index:index + 2], 16) for index in (1, 3, 5))
    return f"\033[{48 if background else 38};2;{red};{green};{blue}m"


@dataclass(frozen=True)
class Theme:
    foreground: str | None = None
    background: str | None = None
    accent: str = "#36c2d6"
    muted: str = "#747474"
    code: str = "#d7ba7d"

    @property
    def base(self) -> str:
        parts: list[str] = []
        if self.foreground:
            parts.append(colour(self.foreground))
        if self.background:
            parts.append(colour(self.background, background=True))
        return "".join(parts)

    @property
    def heading(self) -> str:
        return f"\033[1m{colour(self.accent)}"

    @property
    def code_style(self) -> str:
        return colour(self.code)


THEMES: dict[str, Theme] = {
    "dark": Theme(
        foreground="#d4d4d4",
        background="#000000",
        accent="#36c2d6",
        muted="#747474",
        code="#d7ba7d",
    ),
    "light": Theme(
        foreground="#000000",
        background="#ffffff",
        accent="#36c2d6",
        muted="#747474",
        code="#d7ba7d",
    ),
    "claude": Theme(
        foreground="#e8e8e8",
        background="#1a1a1a",
        accent="#d97757",
        muted="#9b9b9b",
        code="#d7ba7d",
    ),
    "github": Theme(
        foreground="#c9d1d9",
        background="#0d1117",
        accent="#58a6ff",
        muted="#8b949e",
        code="#f0883e",
    ),
    "mono": Theme(
        foreground="#ffffff",
        background="#000000",
        accent="#ffffff",
        muted="#888888",
        code="#dedede",
    ),
    # Dark interfaces inspired by OpenCode, Codex, and VS Code.
    "opencode": Theme(
        foreground="#e7e7e7",
        background="#111111",
        accent="#ffffff",
        muted="#9b9b9b",
        code="#c9d1d9",
    ),
    "codex": Theme(
        foreground="#e5e5e5",
        background="#171717",
        accent="#f5f5f5",
        muted="#999999",
        code="#cccccc",
    ),
    "vscode": Theme(
        foreground="#d4d4d4",
        background="#1e1e1e",
        accent="#ffffff",
        muted="#858585",
        code="#ce9178",
    ),
}


def load_theme(name: str) -> Theme:
    if name == "auto":
        name = "dark"
    if name == "notty":
        return Theme()
    try:
        return THEMES[name]
    except KeyError as error:
        raise ValueError(f"unknown built-in style: {name}") from error
