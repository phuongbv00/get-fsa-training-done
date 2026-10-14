"""Interactive terminal prompts for the lifecycle commands, in the stdlib only.

The package declares no runtime dependencies, so this is a small hand-rolled
take on the `npx skills add` picker: a rail of `◆`/`◇` steps, ↑↓ to move,
space to tick, enter to confirm. Every prompt reads keys from a callable and
writes to a stream, so tests drive it with a list of keys and a `StringIO`;
only `read_key` touches the real terminal.
"""

from __future__ import annotations

import os
import re
import shutil
import sys
from collections.abc import Callable, Sequence
from typing import TextIO

from ..errors import Cancelled

Keys = Callable[[], str]

_UNICODE = {
    "active": "◆",
    "done": "◇",
    "cancel": "■",
    "bar": "│",
    "end": "└",
    "pointer": "❯",
    "on": "●",
    "off": "○",
    "move": "↑↓",
    "h": "─",
    "tr": "┐",
    "br": "┘",
    "ml": "├",
}
_ASCII = {
    "active": "*",
    "done": "o",
    "cancel": "x",
    "bar": "|",
    "end": "+",
    "pointer": ">",
    "on": "(*)",
    "off": "( )",
    "move": "up/down",
    "h": "-",
    "tr": "+",
    "br": "+",
    "ml": "+",
}

_ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")

#: Shown under every question, so leaving is never a guess.
ESC_HINT = "press 'esc' to exit"

#: How many names "Selected:" spells out before it says `+N more`.
SELECTED_SHOWN = 3


def is_interactive() -> bool:
    """True when a person is at a terminal that can answer a prompt."""
    if os.environ.get("CI") or os.environ.get("TERM") == "dumb":
        return False
    try:
        return sys.stdin.isatty() and sys.stdout.isatty()
    except (AttributeError, ValueError):
        return False


# --------------------------------------------------------------------------- keys


def read_key() -> str:
    """One keypress: an arrow, `space`, `enter`, `esc`, or the character."""
    if os.name == "nt":  # pragma: no cover - platform specific
        return _read_key_windows()
    return _read_key_posix()


def _read_key_posix() -> str:  # pragma: no cover - needs a real terminal
    import select
    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        # cbreak, not raw: output processing stays on and Ctrl-C still raises.
        tty.setcbreak(fd)
        ch = os.read(fd, 1)
        if ch == b"\x1b":
            seq = b""
            while len(seq) < 2 and select.select([fd], [], [], 0.05)[0]:
                seq += os.read(fd, 1)
            if not seq:
                return "esc"
            arrows = {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}
            return arrows.get(seq[1:], "") if seq[:1] in (b"[", b"O") else ""
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in (b"\r", b"\n"):
        return "enter"
    if ch == b" ":
        return "space"
    if ch == b"\x03":
        raise KeyboardInterrupt
    return ch.decode("utf-8", "replace")


def _read_key_windows() -> str:  # pragma: no cover - platform specific
    import msvcrt

    ch = msvcrt.getwch()
    if ch in ("\x00", "\xe0"):
        return {"H": "up", "P": "down", "M": "right", "K": "left"}.get(msvcrt.getwch(), "")
    if ch == "\x03":
        raise KeyboardInterrupt
    return {"\r": "enter", " ": "space", "\x1b": "esc"}.get(ch, ch)


def _enable_vt() -> None:  # pragma: no cover - platform specific
    """Let an old Windows console understand the ANSI cursor codes."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except (AttributeError, OSError):
        pass


# ------------------------------------------------------------------------ drawing


class _Screen:
    """Draws a block of lines and redraws it in place."""

    def __init__(self, out: TextIO) -> None:
        self.out = out
        self.drawn = 0
        self.glyph = _glyphs(out)
        self.color = bool(getattr(out, "isatty", lambda: False)())
        self.width = shutil.get_terminal_size((100, 24)).columns
        if self.color:
            _enable_vt()

    def style(self, text: str, code: str) -> str:
        return f"\x1b[{code}m{text}\x1b[0m" if self.color else text

    def draw(self, lines: Sequence[str]) -> None:
        self.clear()
        for line in lines:
            self.out.write(line + "\n")
            # A long line wraps, and every row it takes has to be erased.
            self.drawn += max(1, -(-len(_ANSI.sub("", line)) // self.width))
        self.out.flush()

    def clear(self) -> None:
        if self.drawn:
            self.out.write(f"\x1b[{self.drawn}A\r\x1b[J")
        self.drawn = 0

    def cursor(self, visible: bool) -> None:
        if self.color:
            self.out.write("\x1b[?25h" if visible else "\x1b[?25l")
            self.out.flush()


def _glyphs(out: TextIO) -> dict[str, str]:
    encoding = getattr(out, "encoding", None) or "utf-8"
    try:
        "".join(_UNICODE.values()).encode(encoding)
    except (LookupError, UnicodeEncodeError):
        return _ASCII
    return _UNICODE


def _run(out: TextIO | None, keys: Keys | None, loop: Callable[[_Screen, Keys], object]):
    out = out or sys.stdout
    keys = keys or read_key
    screen = _Screen(out)
    screen.cursor(False)
    try:
        return loop(screen, keys)
    except KeyboardInterrupt:
        raise Cancelled("cancelled") from None
    finally:
        screen.cursor(True)


def _cancelled(screen: _Screen, title: str) -> Cancelled:
    g = screen.glyph
    screen.draw([f"{screen.style(g['cancel'], '31')}  {title}", g["bar"]])
    return Cancelled("cancelled")


def selected_summary(labels: Sequence[str], shown: int = SELECTED_SHOWN) -> str:
    """`A, B, C +2 more`, as the footer of a multi-select spells it."""
    if len(labels) <= shown:
        return ", ".join(labels)
    return ", ".join(labels[:shown]) + f" +{len(labels) - shown} more"


# ------------------------------------------------------------------------ prompts


def step(text: str, *, out: TextIO | None = None, gap: bool = False) -> None:
    """A finished step on the rail: `◇  text`."""
    out = out or sys.stdout
    g = _glyphs(out)
    out.write(f"{g['done']}  {text}\n")
    if gap:
        out.write(g["bar"] + "\n")
    out.flush()


def end(text: str = "", *, out: TextIO | None = None) -> None:
    """Close the rail: `└  text`."""
    out = out or sys.stdout
    g = _glyphs(out)
    out.write(f"{g['end']}  {text}".rstrip() + "\n")
    out.flush()


def note(title: str, lines: Sequence[str], *, out: TextIO | None = None) -> None:
    """A block of information on the rail, with nothing to answer."""
    out = out or sys.stdout
    g = _glyphs(out)
    out.write(f"{g['done']}  {title}\n")
    for line in lines:
        out.write(f"{g['bar']}    {line}\n")
    out.flush()


def multiselect(
    title: str,
    options: Sequence[tuple[str, str]],
    selected: Sequence[int] = (),
    *,
    empty: str = "Select at least one option",
    keys: Keys | None = None,
    out: TextIO | None = None,
) -> list[int]:
    """Tick any number of `(label, detail)` options; returns their indices in order."""
    ticked = set(selected)
    state = {"cursor": 0, "warn": False}

    def render(screen: _Screen) -> list[str]:
        g, bar = screen.glyph, screen.glyph["bar"]
        lines = [
            f"{screen.style(g['active'], '36')}  {screen.style(title, '1')}",
            bar,
            f"{bar}  {screen.style(g['move'] + ' move, space select, enter confirm', '2')}",
            f"{bar}  {screen.style(ESC_HINT, '2')}",
            bar,
        ]
        for i, (label, detail) in enumerate(options):
            mark = screen.style(g["on"], "32") if i in ticked else screen.style(g["off"], "2")
            text = label
            if i == state["cursor"]:
                text = screen.style(label, "4")
            suffix = f" {screen.style('(' + detail + ')', '2')}" if detail else ""
            pointer = screen.style(g["pointer"], "36") if i == state["cursor"] else " "
            lines.append(f"{bar} {pointer} {mark} {text}{suffix}")
        lines.append(bar)
        if state["warn"]:
            lines.append(f"{bar}  {screen.style(empty, '33')}")
        else:
            names = [options[i][0] for i in sorted(ticked)]
            chosen = selected_summary(names) if names else "none"
            lines.append(f"{bar}  {screen.style('Selected:', '32')} {chosen}")
        lines.append(g["end"])
        return lines

    def loop(screen: _Screen, read: Keys) -> list[int]:
        while True:
            screen.draw(render(screen))
            key = read()
            if key == "esc":
                raise _cancelled(screen, title)
            state["warn"] = False
            if key == "up":
                state["cursor"] = (state["cursor"] - 1) % len(options)
            elif key == "down":
                state["cursor"] = (state["cursor"] + 1) % len(options)
            elif key == "space":
                ticked.symmetric_difference_update({state["cursor"]})
            elif key == "enter":
                if not ticked:
                    state["warn"] = True
                    continue
                chosen = sorted(ticked)
                g = screen.glyph
                names = ", ".join(options[i][0] for i in chosen)
                screen.draw(
                    [
                        f"{screen.style(g['done'], '32')}  {title}",
                        f"{g['bar']}  {screen.style(names, '2')}",
                    ]
                )
                return chosen

    return _run(out, keys, loop)


def select(
    title: str,
    options: Sequence[tuple[str, str]],
    default: int = 0,
    *,
    keys: Keys | None = None,
    out: TextIO | None = None,
) -> int:
    """Pick exactly one `(label, detail)` option; returns its index."""
    state = {"cursor": default}

    def render(screen: _Screen) -> list[str]:
        g, bar = screen.glyph, screen.glyph["bar"]
        lines = [
            f"{screen.style(g['active'], '36')}  {screen.style(title, '1')}",
            f"{bar}  {screen.style(g['move'] + ' move, enter confirm', '2')}",
            f"{bar}  {screen.style(ESC_HINT, '2')}",
        ]
        for i, (label, detail) in enumerate(options):
            here = i == state["cursor"]
            mark = screen.style(g["on"], "32") if here else screen.style(g["off"], "2")
            pointer = screen.style(g["pointer"], "36") if here else " "
            text = screen.style(label, "4") if here else label
            suffix = f" {screen.style('(' + detail + ')', '2')}" if detail else ""
            lines.append(f"{bar} {pointer} {mark} {text}{suffix}")
        lines.append(g["end"])
        return lines

    def loop(screen: _Screen, read: Keys) -> int:
        while True:
            screen.draw(render(screen))
            key = read()
            if key == "esc":
                raise _cancelled(screen, title)
            if key == "up":
                state["cursor"] = (state["cursor"] - 1) % len(options)
            elif key == "down":
                state["cursor"] = (state["cursor"] + 1) % len(options)
            elif key == "enter":
                g = screen.glyph
                label = options[state["cursor"]][0]
                screen.draw(
                    [
                        f"{screen.style(g['done'], '32')}  {title}",
                        f"{g['bar']}  {screen.style(label, '2')}",
                    ]
                )
                return state["cursor"]

    return _run(out, keys, loop)


def confirm(
    question: str,
    *,
    default: bool = True,
    keys: Keys | None = None,
    out: TextIO | None = None,
) -> bool:
    """`● Yes / ○ No`: arrows switch, enter answers, `y`/`n` answer at once."""
    state = {"yes": default}

    def loop(screen: _Screen, read: Keys) -> bool:
        g, bar = screen.glyph, screen.glyph["bar"]
        while True:
            yes, no = (g["on"], g["off"]) if state["yes"] else (g["off"], g["on"])
            choice = (
                f"{screen.style(yes, '32' if state['yes'] else '2')} Yes / "
                f"{screen.style(no, '2' if state['yes'] else '32')} No"
            )
            screen.draw(
                [
                    f"{screen.style(g['active'], '36')}  {screen.style(question, '1')}",
                    f"{bar}  {choice}",
                    f"{bar}  {screen.style(ESC_HINT, '2')}",
                    g["end"],
                ]
            )
            key = read()
            if key == "esc":
                raise _cancelled(screen, question)
            if key in ("left", "right", "up", "down"):
                state["yes"] = not state["yes"]
                continue
            answer = {"enter": state["yes"], "y": True, "Y": True, "n": False, "N": False}.get(key)
            if answer is None:
                continue
            word = "Yes" if answer else "No"
            screen.draw(
                [
                    f"{screen.style(g['done'], '32')}  {question}",
                    f"{bar}  {screen.style(word, '2')}",
                ]
            )
            return answer

    return _run(out, keys, loop)


def box(title: str, lines: Sequence[str], *, out: TextIO | None = None) -> None:
    """A framed block on the rail, as `npx skills add` draws its summary.

    `lines` may carry colour from `paint`; widths are measured without it.
    """
    out = out or sys.stdout
    g = _glyphs(out)
    width = shutil.get_terminal_size((100, 24)).columns
    visible = [len(_ANSI.sub("", line)) for line in lines]
    inner = max([len(title) + 4, *(n + 4 for n in visible)])
    inner = max(len(title) + 4, min(inner, width - 2))

    def row(text: str = "", length: int = 0) -> str:
        if length > inner - 4:
            text, length = _ANSI.sub("", text)[: inner - 5] + "…", inner - 4
        return f"{g['bar']}  {text}{' ' * (inner - 2 - length)}{g['bar']}"

    rule = g["h"] * (inner - 3 - len(title))
    out.write(f"{paint(g['done'], '32', out=out)}  {title} {rule}{g['tr']}\n")
    out.write(row() + "\n")
    for line, length in zip(lines, visible, strict=True):
        out.write(row(line, length) + "\n")
    out.write(row() + "\n")
    out.write(f"{g['ml']}{g['h'] * inner}{g['br']}\n")
    out.flush()


def paint(text: str, code: str, *, out: TextIO | None = None) -> str:
    """`text` in an ANSI style when `out` is a terminal, plain otherwise."""
    out = out or sys.stdout
    if getattr(out, "isatty", lambda: False)():
        return f"\x1b[{code}m{text}\x1b[0m"
    return text


__all__ = [
    "Cancelled",
    "box",
    "confirm",
    "end",
    "is_interactive",
    "multiselect",
    "note",
    "paint",
    "read_key",
    "select",
    "selected_summary",
    "step",
]
