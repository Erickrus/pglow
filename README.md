# pglow

A cross-platform terminal Markdown reader. Render Markdown files, stdin, URLs,
and GitHub/GitLab repositories in your terminal with themes, word wrapping, an
interactive pager, and a directory browser — using only the Python standard
library.

## Installation

```bash
pip install .
```

This installs the `pglow` command. You can also run it without installing:

```bash
python -m pglow
```

## Usage

```bash
# Read from a file
pglow README.md

# Read from stdin
echo "# Hello" | pglow -

# Fetch the README from a GitHub or GitLab repository
pglow github.com/charmbracelet/glow

# Fetch Markdown from an HTTP URL
pglow https://example.com/doc.md

# Browse a directory interactively
pglow .
```

Running `pglow` with no arguments opens the interactive browser for the current
directory. Use `pglow <file> --tui` to open a single file in the interactive
viewer.

## Options

```
pglow [source] [-p] [-t] [-s STYLE] [-w WIDTH] [-a] [-l] [-n] [--config PATH]
```

| Flag | Description |
| --- | --- |
| `-p`, `--pager` | Display output with `$PAGER` |
| `-t`, `--tui` | Browse interactively |
| `-s`, `--style` | Theme (see below) |
| `-w`, `--width` | Word wrap width; `0` uses the terminal width |
| `-a`, `--all` | Include hidden files in directory mode |
| `-l`, `--line-numbers` | Show line numbers in TUI mode |
| `-n`, `--preserve-new-lines` | Preserve newlines in the output |
| `--config` | Configuration file path |
| `--version` | Show version |

## Styles

`auto`, `dark`, `light`, `claude`, `github`, `mono`, `opencode`, `codex`,
`vscode`, or `notty` (no colour). When no style is given, `auto` picks `dark`
and plain output is used when the output is not a terminal.

## Configuration

Configuration is read from `~/.config/pglow/pglow.yml` (`%APPDATA%\pglow` on
Windows). The location can be overridden with the `GLOW_CONFIG_HOME`
environment variable.

```yaml
style: auto
pager: false
width: 80
all: false
preserveNewLines: false
showLineNumbers: false
```

## License

MIT
