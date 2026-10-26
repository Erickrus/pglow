"""Configuration loading without a platform-specific dependency."""

import os
import sys
from pathlib import Path

DEFAULT_CONFIG = """# style: auto, dark, light, claude, github, mono, opencode, codex, vscode, or notty
style: auto
pager: false
width: 80
all: false
preserveNewLines: false
showLineNumbers: false
"""


def config_dir() -> Path:
    """Return the native user configuration location for the current OS."""
    if override := os.environ.get("GLOW_CONFIG_HOME"):
        return Path(override).expanduser()
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming")) / "pglow"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "pglow"


def config_path(explicit: str | None = None) -> Path:
    return Path(explicit).expanduser() if explicit else config_dir() / "pglow.yml"


def load_config(path: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value.lower() in ("true", "false"):
            values[key] = value.lower() == "true"
        elif value.isdigit():
            values[key] = int(value)
        else:
            values[key] = value
    return values


def ensure_config(path: Path) -> None:
    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(DEFAULT_CONFIG, encoding="utf-8")
