"""Virtual editor: buffer + cursor + search, driven by vim-style commands."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import motions
from .buffer import Buffer
from .search import SearchSession

# Motion family per command key (for mastery tracking).
FAMILIES: dict[str, str] = {
    "h": "character",
    "j": "character",
    "k": "character",
    "l": "character",
    "w": "word",
    "b": "word",
    "e": "word",
    "0": "line",
    "^": "line",
    "$": "line",
    "gg": "document",
    "G": "document",
    "f": "find",
    "t": "find",
    "/": "search",
    "n": "search",
    "N": "search",
}

VALID_KEYS = set(FAMILIES)


@dataclass
class CommandResult:
    command: str
    key: str  # base motion key (h, w, f, /, ...)
    family: str
    moved: bool
    invalid: bool
    pos: tuple[int, int]


@dataclass
class VirtualEditor:
    lines: list[str]
    start: tuple[int, int] = (0, 0)
    buf: Buffer = field(init=False)
    search: SearchSession = field(init=False)
    history: list[CommandResult] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.buf = Buffer.from_lines(self.lines, *self.start)
        self.search = SearchSession(self.buf.lines)

    @property
    def pos(self) -> tuple[int, int]:
        return self.buf.pos

    def apply(self, command: str, allowed: set[str] | None = None) -> CommandResult:
        """Apply one command string (e.g. 'w', '3j', 'f,', '/dragon', 'gg').

        `allowed`: permitted base keys; a command with a disallowed key is
        recorded as invalid and has no effect.
        A motion that does not move the cursor is also invalid (no-op).
        """
        key, count, arg = _parse(command)
        family = FAMILIES.get(key, "")
        if key == "" or key not in VALID_KEYS:
            res = CommandResult(command, key, family, False, True, self.pos)
            self.history.append(res)
            return res
        if allowed is not None and key not in allowed:
            res = CommandResult(command, key, family, False, True, self.pos)
            self.history.append(res)
            return res

        moved = self._execute(key, count, arg)
        res = CommandResult(command, key, family, moved, not moved, self.pos)
        self.history.append(res)
        return res

    def _execute(self, key: str, count: int, arg: str) -> bool:
        buf = self.buf
        if key == "h":
            return motions.move_h(buf, count)
        if key == "l":
            return motions.move_l(buf, count)
        if key == "j":
            return motions.move_j(buf, count)
        if key == "k":
            return motions.move_k(buf, count)
        if key == "w":
            return motions.move_w(buf, count)
        if key == "b":
            return motions.move_b(buf, count)
        if key == "e":
            return motions.move_e(buf, count)
        if key == "0":
            return motions.move_0(buf)
        if key == "^":
            return motions.move_caret(buf)
        if key == "$":
            return motions.move_dollar(buf)
        if key == "gg":
            return motions.move_gg(buf)
        if key == "G":
            return motions.move_G(buf)
        if key == "f":
            return motions.move_f(buf, arg)
        if key == "t":
            return motions.move_t(buf, arg)
        if key == "/":
            target = self.search.search(arg, self.pos)
            if target is None:
                return False
            buf.set_pos(*target)
            # A search counts as an action even when the cursor is already
            # on the first match (the target is still visited).
            return True
        if key == "n":
            target = self.search.next(self.pos)
            if target is None:
                return False
            buf.set_pos(*target)
            return True
        if key == "N":
            target = self.search.prev(self.pos)
            if target is None:
                return False
            buf.set_pos(*target)
            return True
        return False


def _parse(command: str) -> tuple[str, int, str]:
    """Parse a command into (base key, count, arg).

    Examples: 'w' -> ('w', 1, ''), '3j' -> ('j', 3, ''),
    'f,' -> ('f', 1, ','), '/dragon' -> ('/', 1, 'dragon').
    Returns ('', 1, '') for unparseable input.
    """
    if not command:
        return ("", 1, "")
    if command.startswith("/"):
        return ("/", 1, command[1:])
    if command in ("gg", "G", "n", "N", "^", "$", "0"):
        return (command, 1, "")
    # count prefix
    i = 0
    while i < len(command) and command[i].isdigit():
        i += 1
    count = int(command[:i]) if i else 1
    rest = command[i:]
    if rest in ("h", "j", "k", "l", "w", "b", "e"):
        return (rest, count, "")
    if len(rest) == 2 and rest[0] in ("f", "t"):
        return (rest[0], count, rest[1])
    return ("", 1, "")
