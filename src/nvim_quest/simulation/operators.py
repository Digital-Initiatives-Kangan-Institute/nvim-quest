"""Vim-like edit operators (d/c/y with motions, x, p, .) over text ranges.

Scope notes (MVP simplifications, documented for level authors):
- Charwise operator ranges may span lines for `w`/`e` (lines are joined,
  vim-like). All other charwise motions stay on the cursor's line.
- `cw` behaves like `ce` (to word end), matching real vim.
- `P`, visual mode, and `u` are out of scope.
- Counts multiply: `d2w` deletes two words, `2dd` deletes two lines.
- `iw` (inner word) accepts no count.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import motions
from .buffer import Buffer


@dataclass
class Register:
    """Yank/delete product: text lines + linewise flag for `p` placement."""

    lines: list[str] = field(default_factory=list)
    linewise: bool = False


@dataclass
class LastChange:
    """Repeatable edit for `.`: operator + motion + inserted text/count."""

    op: str  # d, c, x, p
    motion: str = ""  # motion spec ("" for x), or snapshot for p
    count: int = 1
    inserted: str = ""
    put_lines: list[str] = field(default_factory=list)
    put_linewise: bool = False


LINEWISE_MOTIONS = {"j", "k", "G", "gg"}
CHAR_MOTIONS = {"h", "l", "w", "b", "e", "0", "^", "$", "G", "gg", "f", "t"}


def parse_motion(spec: str) -> tuple[str, int, str] | None:
    """Parse an operator motion into (key, count, arg).

    Accepts h j k l w b e 0 ^ $ gg G, f<char>, t<char>, and iw.
    Returns None for anything else (including counts on iw).
    """
    if spec in ("gg", "iw"):
        return (spec, 1, "")
    if spec in CHAR_MOTIONS:
        return (spec, 1, "")
    if len(spec) == 2 and spec[0] in ("f", "t"):
        return (spec[0], 1, spec[1])
    i = 0
    while i < len(spec) and spec[i].isdigit():
        i += 1
    if not i:
        return None
    count = int(spec[:i])
    rest = spec[i:]
    if rest in CHAR_MOTIONS or rest == "gg":
        return (rest, count, "")
    if len(rest) == 2 and rest[0] in ("f", "t"):
        return (rest[0], count, rest[1])
    return None


def _iw_range(lines: list[str], row: int, col: int) -> tuple[int, int] | None:
    """Inner-word span on the current line; None on whitespace/empty."""
    line = lines[row]
    if not line or col >= len(line) or line[col].isspace():
        return None
    cls = motions._classify(line[col])
    start = col
    while start > 0 and motions._classify(line[start - 1]) == cls:
        start -= 1
    end = col
    while end + 1 < len(line) and motions._classify(line[end + 1]) == cls:
        end += 1
    return (start, end + 1)


def _run_motion(
    buf: Buffer, mkey: str, mcount: int, marg: str
) -> tuple[int, int] | None:
    """Target position of a motion from the buffer cursor (no mutation)."""
    clone = Buffer.from_lines(list(buf.lines), buf.row, buf.col)
    moved = False
    if mkey == "h":
        moved = motions.move_h(clone, mcount)
    elif mkey == "l":
        moved = motions.move_l(clone, mcount)
    elif mkey == "j":
        moved = motions.move_j(clone, mcount)
    elif mkey == "k":
        moved = motions.move_k(clone, mcount)
    elif mkey == "w":
        moved = motions.move_w(clone, mcount)
    elif mkey == "b":
        moved = motions.move_b(clone, mcount)
    elif mkey == "e":
        moved = motions.move_e(clone, mcount)
    elif mkey == "0":
        moved = motions.move_0(clone)
    elif mkey == "^":
        moved = motions.move_caret(clone)
    elif mkey == "$":
        moved = motions.move_dollar(clone)
    elif mkey == "gg":
        moved = motions.move_gg(clone)
    elif mkey == "G":
        moved = motions.move_G(clone)
    elif mkey == "f":
        moved = motions.move_f(clone, marg)
    elif mkey == "t":
        moved = motions.move_t(clone, marg)
    return clone.pos if moved else None


def motion_range(
    buf: Buffer, mkey: str, mcount: int, marg: str, op: str = "d"
) -> tuple[tuple[tuple[int, int], tuple[int, int]], bool] | None:
    """Compute ((start, end_exclusive), linewise) for op + motion.

    Returns None when the motion goes nowhere (operator is a no-op).
    `cw` targets the word end like `ce`.
    """
    if op == "c" and mkey == "w":
        mkey = "e"  # vim special case: cw behaves like ce
    if mkey == "iw":
        span = _iw_range(buf.lines, buf.row, buf.col)
        if span is None:
            return None
        return (((buf.row, span[0]), (buf.row, span[1])), False)
    if mkey in LINEWISE_MOTIONS:
        target = _run_motion(buf, mkey, mcount, marg)
        if target is None:
            return None
        lo = min(buf.row, target[0])
        hi = max(buf.row, target[0])
        return (((lo, 0), (hi, 0)), True)

    target = _run_motion(buf, mkey, mcount, marg)
    if target is None:
        if mkey != "w":
            return None
        # `w` at the end of the line/buffer: delete to the end of the
        # current word run instead of no-op (matches vim's `dw`).
        (sr, sc) = buf.pos
        line = buf.lines[sr]
        if sc >= len(line) or line[sc].isspace():
            return None
        cls = motions._classify(line[sc])
        end = sc
        while end < len(line) and motions._classify(line[end]) == cls:
            end += 1
        return (((sr, sc), (sr, end)), False)
    (sr, sc) = buf.pos
    (tr, tc) = target
    line_len = len(buf.lines[sr])
    if mkey in ("b", "0", "^", "h"):
        # Backward: include the cursor character.
        return (((tr, tc), (sr, min(sc + 1, line_len))), False)
    if mkey in ("e", "f"):
        # Inclusive: end one past the target character.
        return (((sr, sc), (tr, tc + 1)), False)
    if mkey == "$":
        return (((sr, sc), (sr, line_len)), False)
    # Exclusive forward: w, t, l.
    return (((sr, sc), (tr, tc)), False)


def span_text(
    lines: list[str], start: tuple[int, int], end: tuple[int, int]
) -> list[str]:
    """Text of a charwise range as lines (single entry if one line)."""
    (r1, c1), (r2, c2) = start, end
    if r1 == r2:
        return [lines[r1][c1:c2]]
    out = [lines[r1][c1:]]
    out.extend(lines[r1 + 1 : r2])
    out.append(lines[r2][:c2])
    return out
