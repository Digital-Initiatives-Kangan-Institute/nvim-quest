"""Vim-like motion implementations.

Each motion takes a Buffer and an optional count, mutates the buffer,
and returns True if the cursor moved.
"""

from __future__ import annotations

import string

from .buffer import Buffer

_WORD_CHARS = set(string.ascii_letters + string.digits + "_")


def _classify(ch: str) -> str:
    """Classify a character: 'word', 'punct', or 'space'."""
    if ch == "" or ch.isspace():
        return "space"
    if ch in _WORD_CHARS:
        return "word"
    return "punct"


def _char_at(lines: list[str], row: int, col: int) -> str:
    if 0 <= row < len(lines) and 0 <= col < len(lines[row]):
        return lines[row][col]
    return ""


def _is_last_position(lines: list[str], row: int, col: int) -> bool:
    return row == len(lines) - 1 and col >= max(0, len(lines[row]) - 1)


def _next_pos(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    """Next cursor position (crossing lines); None if at end of buffer."""
    if col + 1 < len(lines[row]):
        return (row, col + 1)
    if row + 1 < len(lines):
        return (row + 1, 0)
    return None


def _prev_pos(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    if col > 0:
        return (row, col - 1)
    if row > 0:
        prev = lines[row - 1]
        return (row - 1, max(0, len(prev) - 1))
    return None


# --- character motions -----------------------------------------------------


def move_h(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    buf.set_pos(buf.row, buf.col - count)
    return buf.pos != old


def move_l(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    buf.set_pos(buf.row, buf.col + count)
    return buf.pos != old


def move_j(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    row = min(buf.num_lines - 1, buf.row + count)
    buf.row = row
    buf.col = min(buf.preferred_col, buf.max_col(row))
    return buf.pos != old


def move_k(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    row = max(0, buf.row - count)
    buf.row = row
    buf.col = min(buf.preferred_col, buf.max_col(row))
    return buf.pos != old


# --- word motions ----------------------------------------------------------


def _w_once(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    """One `w`: move to start of next word (word or punctuation run)."""
    pos = _next_pos(lines, row, col)
    # Skip remainder of current word/punct run. A newline always ends the
    # run (lines[...] has no newline char, so check row changes explicitly).
    cur = _classify(_char_at(lines, row, col))
    while pos is not None and cur != "space":
        if pos[0] != row:
            break
        nxt = _classify(_char_at(lines, *pos))
        if nxt != cur:
            break
        row, col = pos
        pos = _next_pos(lines, row, col)
    # Skip whitespace (crossing empty lines) to next word start.
    while pos is not None and _classify(_char_at(lines, *pos)) == "space":
        row, col = pos
        pos = _next_pos(lines, row, col)
    return pos


def _e_once(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    """One `e`: move to end of current-or-next word."""
    pos = _next_pos(lines, row, col)
    if pos is None:
        return None
    # If currently on last char of a word (next is space/other), skip spaces first.
    cur = _classify(_char_at(lines, row, col))
    nxt = _classify(_char_at(lines, *pos))
    if cur != "space" and nxt != cur:
        # At word end already -> skip whitespace to start of next word.
        p = pos
        while p is not None and _classify(_char_at(lines, *p)) == "space":
            p = _next_pos(lines, *p)
        if p is None:
            return None
        row, col = p
        pos = _next_pos(lines, row, col)
    else:
        row, col = pos
        pos = _next_pos(lines, row, col)
    # Advance to end of this word run. A newline always ends the run,
    # even mid-class (vim word motions stop at line ends here).
    cur = _classify(_char_at(lines, row, col))
    while (
        pos is not None
        and pos[0] == row
        and _classify(_char_at(lines, *pos)) == cur
    ):
        row, col = pos
        pos = _next_pos(lines, row, col)
    return (row, col)


def _b_once(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    """One `b`: move to start of current-or-previous word."""
    # If at a word start (prev is space/different), step back first.
    pos = (row, col)
    cur = _classify(_char_at(lines, row, col))
    prev = _prev_pos(lines, row, col)
    # A newline always separates words: reaching across rows counts as
    # being at a word start.
    at_start = (
        prev is None
        or prev[0] != row
        or _classify(_char_at(lines, *prev)) != cur
        or cur == "space"
    )
    if at_start:
        if prev is None:
            return None
        row, col = prev
        # Skip whitespace backwards.
        while _classify(_char_at(lines, row, col)) == "space":
            prev = _prev_pos(lines, row, col)
            if prev is None:
                return None
            row, col = prev
    # Now inside (or at end of) a word: walk back to its start,
    # never crossing into the previous line's words.
    cur = _classify(_char_at(lines, row, col))
    prev = _prev_pos(lines, row, col)
    while (
        prev is not None
        and prev[0] == row
        and _classify(_char_at(lines, *prev)) == cur
    ):
        row, col = prev
        prev = _prev_pos(lines, row, col)
    return (row, col)


def move_w(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    row, col = old
    for _ in range(count):
        nxt = _w_once(buf.lines, row, col)
        if nxt is None:
            break
        row, col = nxt
    buf.set_pos(row, col)
    return buf.pos != old


def move_e(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    row, col = old
    for _ in range(count):
        nxt = _e_once(buf.lines, row, col)
        if nxt is None:
            break
        row, col = nxt
    buf.set_pos(row, col)
    return buf.pos != old


def move_b(buf: Buffer, count: int = 1) -> bool:
    old = buf.pos
    row, col = old
    for _ in range(count):
        nxt = _b_once(buf.lines, row, col)
        if nxt is None:
            break
        row, col = nxt
    buf.set_pos(row, col)
    return buf.pos != old


# --- line motions ----------------------------------------------------------


def move_0(buf: Buffer) -> bool:
    old = buf.pos
    buf.set_pos(buf.row, 0)
    return buf.pos != old


def move_caret(buf: Buffer) -> bool:
    """`^`: first non-blank character of the line."""
    old = buf.pos
    line = buf.line(buf.row)
    col = len(line) - len(line.lstrip())
    if col >= len(line):
        col = 0
    buf.set_pos(buf.row, col)
    return buf.pos != old


def move_dollar(buf: Buffer) -> bool:
    """`$`: end of line (last character)."""
    old = buf.pos
    buf.set_pos(buf.row, buf.max_col(buf.row))
    return buf.pos != old


# --- document motions ------------------------------------------------------


def move_gg(buf: Buffer) -> bool:
    old = buf.pos
    buf.row = 0
    buf.clamp()
    move_caret(buf)
    return buf.pos != old


def move_G(buf: Buffer) -> bool:
    old = buf.pos
    buf.row = buf.num_lines - 1
    buf.clamp()
    # Land on first non-blank like vim, unless line is blank.
    line = buf.line(buf.row)
    if line.strip():
        move_caret(buf)
    return buf.pos != old


# --- find motions (current line only) --------------------------------------


def move_f(buf: Buffer, char: str) -> bool:
    """`f<char>`: onto next occurrence on current line."""
    old = buf.pos
    line = buf.line(buf.row)
    idx = line.find(char, buf.col + 1)
    if idx == -1:
        return False
    buf.set_pos(buf.row, idx)
    return buf.pos != old


def move_t(buf: Buffer, char: str) -> bool:
    """`t<char>`: immediately before next occurrence on current line."""
    old = buf.pos
    line = buf.line(buf.row)
    idx = line.find(char, buf.col + 1)
    if idx == -1 or idx - 1 <= buf.col:
        return False
    buf.set_pos(buf.row, idx - 1)
    return buf.pos != old
