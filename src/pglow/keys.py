"""Raw terminal key input without a platform-specific UI library."""

import os
import select
import sys
import time

from .terminal import enable_windows_ansi


class KeyReader:
    """Read named keys without relying on a platform-specific UI library."""

    def __enter__(self) -> "KeyReader":
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise ValueError("the TUI requires an interactive terminal")
        enable_windows_ansi()
        if sys.platform != "win32":
            import termios
            import tty

            self._termios = termios
            self._fd = sys.stdin.fileno()
            self._state = termios.tcgetattr(self._fd)
            # cbreak disables line buffering and echo but keeps output newline
            # processing enabled. Raw mode turns off OPOST and makes each
            # redraw start at the previous line's column.
            tty.setcbreak(self._fd)
            sys.stdout.write("\033[?25l")
            sys.stdout.flush()
        return self

    def __exit__(self, *_: object) -> None:
        if sys.platform != "win32":
            self._termios.tcsetattr(self._fd, self._termios.TCSADRAIN, self._state)
            sys.stdout.write("\033[0m\033[?25h\n")
            sys.stdout.flush()

    def read(self, timeout: float | None = None) -> str | None:
        if sys.platform == "win32":
            import msvcrt

            deadline = None if timeout is None else time.monotonic() + timeout
            while not msvcrt.kbhit():
                if deadline is not None and time.monotonic() >= deadline:
                    return None
                time.sleep(0.01)
            key = msvcrt.getwch()
            if key in ("\x00", "\xe0"):
                return {"H": "up", "P": "down", "I": "pageup", "O": "pagedown"}.get(
                    msvcrt.getwch(), ""
                )
            return {"\r": "enter", "\x03": "quit", "\x1b": "quit"}.get(key, key)

        if not select.select([sys.stdin], [], [], timeout)[0]:
            return None
        key = os.read(sys.stdin.fileno(), 1).decode("utf-8", "replace")
        if key != "\x1b":
            return {"\r": "enter", "\n": "enter", "\x03": "quit"}.get(key, key)
        # Terminal emulators can deliver an escape sequence one byte at a time.
        # Read the CSI prefix and its final byte with a generous short timeout
        # instead of interpreting a partially received arrow key as Escape.
        if not select.select([sys.stdin], [], [], 0.15)[0]:
            return "quit"
        sequence = os.read(sys.stdin.fileno(), 1).decode("ascii", "ignore")
        while not sequence.endswith(("~", "A", "B", "C", "D")):
            if not select.select([sys.stdin], [], [], 0.15)[0]:
                return ""
            sequence += os.read(sys.stdin.fileno(), 1).decode("ascii", "ignore")
        return {"[A": "up", "[B": "down", "[5~": "pageup", "[6~": "pagedown"}.get(
            sequence, ""
        )
