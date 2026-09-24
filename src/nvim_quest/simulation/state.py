"""Virtual editor: buffer + cursor + search, driven by vim-style commands."""

from __future__ import annotations

from dataclasses import dataclass, field

from . import motions
from . import operators
from .buffer import Buffer
from .operators import LastChange, Register
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
    "x": "edit",
    "d": "edit",
    "c": "edit",
    "y": "edit",
    "p": "edit",
    ".": "edit",
}

VALID_KEYS = set(FAMILIES)


@dataclass
class CommandResult:
    command: str
    key: str  # base motion key (h, w, f, /, ...) or operator (d, c, x, ...)
    family: str
    moved: bool
    invalid: bool
    pos: tuple[int, int]
    enter_insert: bool = False  # change operator committed, type to finish


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
        self.unnamed: Register | None = None
        self.last_change: LastChange | None = None
        self.awaiting_insert = False
        self._pending_change: tuple[str, int] | None = None  # (motion, count)
        # Raw deletion point for the pending insert. This is NOT the cursor:
        # delete_* clamps the cursor to the shortened line, but typed text
        # must go exactly where the deletion started (e.g. end of line).
        self._insert_pos: tuple[int, int] | None = None

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
        if self.awaiting_insert:
            # A change was never finished with typed text: commit it empty
            # before processing the new command (deterministic replay).
            self.commit_insert("")

        moved = self._execute(key, count, arg)
        entered = key == "c" and moved and self.awaiting_insert
        res = CommandResult(command, key, family, moved, not moved, self.pos,
                            entered)
        self.history.append(res)
        return res

    def commit_insert(self, text: str) -> bool:
        """Finish a pending change with typed text. Returns False when
        nothing was pending."""
        if not self.awaiting_insert or self._pending_change is None:
            return False
        motion, count = self._pending_change
        pos = self._insert_pos or (self.buf.row, self.buf.col)
        if text:
            self.buf.insert_text(pos[0], pos[1], text)
        self.last_change = LastChange(op="c", motion=motion, count=count,
                                      inserted=text)
        self.awaiting_insert = False
        self._pending_change = None
        self._insert_pos = None
        self._mutated()
        return True

    def _mutated(self) -> None:
        """Re-sync search state after text changes (matches go stale)."""
        self.search.lines = self.buf.lines
        self.search.matches = []
        self.search.index = -1

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
        if key in ("d", "c", "y"):
            return self._edit(key, count, arg)
        if key == "x":
            return self._delete_char(count)
        if key == "p":
            return self._put(count)
        if key == ".":
            return self._repeat()
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

    # -- edit operators ----------------------------------------------------

    def _edit(self, op: str, count: int, motion: str) -> bool:
        """Apply d/c/y with a motion spec (or "line" for dd/yy)."""
        buf = self.buf
        if motion == "line":
            if op == "c":
                return False  # cc out of scope
            if op == "y":
                self.unnamed = Register(
                    lines=list(buf.lines[buf.row : buf.row + count]),
                    linewise=True,
                )
                return True
            removed = buf.delete_lines(buf.row, count)
            self.unnamed = Register(lines=removed, linewise=True)
            self.last_change = LastChange(op="d", motion="line", count=count)
            self._mutated()
            return True
        parsed = operators.parse_motion(motion)
        if parsed is None:
            return False
        mkey, mcount, marg = parsed
        total = count * mcount
        if mkey == "iw" and total != 1:
            return False
        rng = operators.motion_range(buf, mkey, total, marg, op)
        if rng is None:
            return False
        (start, end), linewise = rng
        if linewise:
            rows = list(range(start[0], end[0] + 1))
            yanked = [buf.lines[r] for r in rows]
            if op == "y":
                self.unnamed = Register(lines=yanked, linewise=True)
                return True
            removed = buf.delete_lines(start[0], len(rows))
            self.unnamed = Register(lines=removed, linewise=True)
            if op == "c":
                self._begin_insert(motion, count, self.buf.pos)
            else:
                self.last_change = LastChange(op="d", motion=motion,
                                              count=count)
            self._mutated()
            return True
        text = operators.span_text(buf.lines, start, end)
        if op == "y":
            if all(t == "" for t in text):
                return False
            self.unnamed = Register(lines=text, linewise=False)
            return True
        removed = buf.delete_span(start, end)
        if removed == "":
            return False
        self.unnamed = Register(lines=[removed], linewise=False)
        if op == "c":
            self._begin_insert(motion, count, start)
        else:
            self.last_change = LastChange(op="d", motion=motion, count=count)
        self._mutated()
        return True

    def _begin_insert(self, motion: str, count: int,
                      pos: tuple[int, int]) -> None:
        self.awaiting_insert = True
        self._pending_change = (motion, count)
        self._insert_pos = pos

    def _delete_char(self, count: int) -> bool:
        removed = self.buf.delete_char(count)
        if removed == "":
            return False
        self.unnamed = Register(lines=[removed], linewise=False)
        self.last_change = LastChange(op="x", count=count)
        self._mutated()
        return True

    def _put(self, count: int) -> bool:
        reg = self.unnamed
        if reg is None or not reg.lines:
            return False
        if not reg.linewise and all(l == "" for l in reg.lines):
            return False
        buf = self.buf
        if reg.linewise:
            copies: list[str] = []
            for _ in range(count):
                copies.extend(reg.lines)
            for i, line in enumerate(copies):
                buf.lines.insert(buf.row + 1 + i, line)
            first = buf.lines[buf.row + 1]
            indent = len(first) - len(first.lstrip())
            buf.set_pos(buf.row + 1, indent if indent < len(first) else 0)
        else:
            text = reg.lines[0] * count
            line = buf.lines[buf.row]
            if line == "":
                buf.lines[buf.row] = text
                buf.set_pos(buf.row, max(0, len(text) - 1))
            else:
                col = buf.col
                buf.lines[buf.row] = line[: col + 1] + text + line[col + 1 :]
                buf.set_pos(buf.row, col + len(text))
        self.last_change = LastChange(op="p", count=count,
                                      put_lines=list(reg.lines),
                                      put_linewise=reg.linewise)
        self._mutated()
        return True

    def _repeat(self) -> bool:
        lc = self.last_change
        if lc is None:
            return False
        if lc.op == "x":
            return self._delete_char(lc.count)
        if lc.op == "p":
            return self._repeat_put(lc)
        if lc.op in ("d", "c"):
            return self._repeat_edit(lc)
        return False

    def _repeat_put(self, lc: LastChange) -> bool:
        saved = self.unnamed
        self.unnamed = Register(lines=list(lc.put_lines),
                                linewise=lc.put_linewise)
        ok = self._put(lc.count)
        if not ok:
            self.unnamed = saved
        return ok

    def _repeat_edit(self, lc: LastChange) -> bool:
        if lc.motion == "line":
            if lc.op == "d":
                self.buf.delete_lines(self.buf.row, lc.count)
                self._mutated()
                return True
            return False
        parsed = operators.parse_motion(lc.motion)
        if parsed is None:
            return False
        mkey, mcount, marg = parsed
        rng = operators.motion_range(self.buf, mkey, mcount * lc.count,
                                     marg, lc.op)
        if rng is None:
            return False
        (start, end), linewise = rng
        if linewise:
            rows = list(range(start[0], end[0] + 1))
            self.buf.delete_lines(start[0], len(rows))
            if lc.op == "c" and lc.inserted:
                self.buf.insert_text(self.buf.row, self.buf.col,
                                     lc.inserted)
            self._mutated()
            return True
        removed = self.buf.delete_span(start, end)
        if removed == "":
            return False
        if lc.op == "c" and lc.inserted:
            self.buf.insert_text(start[0], start[1], lc.inserted)
        self._mutated()
        return True


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
    if rest in ("x", "p", "."):
        return (rest, count, "")
    if rest and rest[0] in ("d", "c", "y"):
        op = rest[0]
        tail = rest[1:]
        if tail == op and op in ("d", "y"):
            return (op, count, "line")  # dd, yy (cc out of scope)
        return (op, count, tail)  # motion spec; "" = incomplete operator
    if len(rest) == 2 and rest[0] in ("f", "t"):
        return (rest[0], count, rest[1])
    return ("", 1, "")
