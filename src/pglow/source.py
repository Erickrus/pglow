"""Input source resolution for files, streams, URLs, and repositories."""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from ._version import __version__

README_NAMES = ("readme", "readme.md")
USER_AGENT = f"pglow/{__version__}"


@dataclass(frozen=True)
class Source:
    content: str
    name: str


def _request(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                raise ValueError(f"HTTP status {response.status}")
            return response.read()
    except HTTPError as error:
        raise ValueError(f"HTTP status {error.code} for {url}") from error
    except URLError as error:
        raise ValueError(f"unable to fetch {url}: {error.reason}") from error


def repository_readme(url: str) -> str | None:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2:
        return None
    owner, repo = parts
    if parsed.hostname == "github.com":
        api = f"https://api.github.com/repos/{owner}/{repo}/readme"
        return json.loads(_request(api))["download_url"]
    if parsed.hostname == "gitlab.com":
        project = quote(f"{owner}/{repo}", safe="")
        api = f"https://gitlab.com/api/v4/projects/{project}"
        readme_url = json.loads(_request(api)).get("readme_url")
        return readme_url.replace("/blob/", "/raw/") if readme_url else None
    return None


def _remove_frontmatter(content: str) -> str:
    if not content.startswith("---\n") and not content.startswith("---\r\n"):
        return content
    marker_end = content.find("\n---", 4)
    if marker_end == -1:
        return content
    end_of_line = content.find("\n", marker_end + 1)
    return content[end_of_line + 1:] if end_of_line != -1 else ""


def discover_markdown(directory: Path, include_hidden: bool = False) -> list[Path]:
    files: list[Path] = []
    for path in directory.rglob("*"):
        if not path.is_file() or (
            not include_hidden
            and any(part.startswith(".") for part in path.parts)
        ):
            continue
        if path.suffix.lower() in (".md", ".mdown", ".mkdn", ".mkd", ".markdown"):
            files.append(path)
    return sorted(files, key=lambda item: str(item).lower())


def from_argument(argument: str) -> Source:
    if argument == "-":
        return Source(_remove_frontmatter(sys.stdin.read()), "stdin")
    parsed = urlparse(argument)
    if parsed.scheme:
        readme = repository_readme(argument)
        url = readme if readme else argument
        return Source(_remove_frontmatter(_request(url).decode("utf-8", "replace")), url)
    path = Path(argument).expanduser()
    if not path.is_file():
        raise ValueError(f"unable to open file: {path}")
    return Source(
        _remove_frontmatter(path.read_text(encoding="utf-8", errors="replace")),
        str(path.resolve()),
    )
