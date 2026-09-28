"""Virtual text buffer with cursor management (vim-like)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Buffer:
    lines: list[str] = field(default_factory=lambda: [""])
    row: int = 0
    col: int = 0
    preferred_col: int = 0  # remembered column for j/k vertical moves

    @classmethod
    def from_lines(cls, lines: list[str], row: int = 0, col: int = 0) -> "Buffer":
        if not lines:
            lines = [""]
        buf = cls(lines=list(lines), row=row, col=col, preferred_col=col)
        buf.clamp()
        buf.preferred_col = buf.col
        return buf

    @property
    def num_lines(self) -> int:
        return len(self.lines)

    def line(self, row: int) -> str:
        return self.lines[row]

    def line_len(self, row: int) -> int:
        return len(self.lines[row])

    def max_col(self, row: int) -> int:
        """Maximum cursor column on a row (last char index; 0 for empty line)."""
        return max(0, len(self.lines[row]) - 1)

    def clamp(self) -> None:
        self.row = max(0, min(self.row, self.num_lines - 1))
        self.col = max(0, min(self.col, self.max_col(self.row)))

    @property
    def pos(self) -> tuple[int, int]:
        return (self.row, self.col)

    def set_pos(self, row: int, col: int, remember_col: bool = True) -> None:
        self.row = row
        self.col = col
        self.clamp()
        if remember_col:
            self.preferred_col = self.col

    def char_at(self, row: int, col: int) -> str:
        line = self.lines[row]
        if 0 <= col < len(line):
            return line[col]
        return ""

    # -- mutation (all in-place; callers re-sync search state) ---------------

    def delete_char(self, count: int = 1) -> str:
        """Delete `count` chars under the cursor. Returns removed text."""
        line = self.lines[self.row]
        if not line:
            return ""
        end = min(len(line), self.col + count)
        removed = line[self.col : end]
        self.lines[self.row] = line[: self.col] + line[end:]
        self.clamp()
        return removed

    def replace_char(self, count: int, char: str) -> str:
        """Overwrite `count` chars at the cursor with `char` (no shifting).
        Cursor stays put. Returns replaced text ("" when nothing there)."""
        line = self.lines[self.row]
        if not line or self.col >= len(line):
            return ""
        end = min(len(line), self.col + count)
        removed = line[self.col : end]
        self.lines[self.row] = (
            line[: self.col] + char * (end - self.col) + line[end:]
        )
        self.clamp()
        return removed

    def join_lines(self, row: int, count: int = 1) -> bool:
        """Join `count` following lines into `row` with single spaces.

        Next-line indent is stripped; blank lines add nothing. Cursor
        stays (clamped). False when there is no next line.
        """
        if row + 1 >= len(self.lines):
            return False
        merged = 0
        while merged < count and row + 1 < len(self.lines):
            nxt = self.lines.pop(row + 1)
            self.lines[row] += (" " + nxt.lstrip() if nxt.strip() else "")
            merged += 1
        self.clamp()
        return merged > 0

    def delete_span(
        self, start: tuple[int, int], end: tuple[int, int]
    ) -> str:
        """Delete charwise range [start, end), possibly across lines
        (lines are joined, vim-like). Cursor lands on `start`."""
        (r1, c1), (r2, c2) = start, end
        if (r1, c1) == (r2, c2):
            return ""
        if r1 == r2:
            line = self.lines[r1]
            removed = line[c1:c2]
            self.lines[r1] = line[:c1] + line[c2:]
        else:
            removed = self.lines[r1][c1:]
            for r in range(r1 + 1, r2):
                removed += "\n" + self.lines[r]
            removed += "\n" + self.lines[r2][:c2]
            self.lines[r1] = self.lines[r1][:c1] + self.lines[r2][c2:]
            del self.lines[r1 + 1 : r2 + 1]
        self.set_pos(r1, c1)
        return removed

    def delete_lines(self, row: int, count: int = 1) -> list[str]:
        """Delete `count` whole lines from `row`. Never removes the final
        line (leaves one empty line). Cursor goes to the first non-blank
        of the line now at that position."""
        count = max(1, min(count, len(self.lines) - row))
        removed = self.lines[row : row + count]
        del self.lines[row : row + count]
        if not self.lines:
            self.lines = [""]
        row = min(row, len(self.lines) - 1)
        line = self.lines[row]
        indent = len(line) - len(line.lstrip())
        self.set_pos(row, indent if indent < len(line) else 0)
        return removed

    def insert_text(self, row: int, col: int, text: str) -> tuple[int, int]:
        """Insert text (possibly multi-line) at (row, col).
        Returns the new cursor position (end of inserted text)."""
        before = self.lines[row][:col]
        after = self.lines[row][col:]
        parts = text.split("\n")
        if len(parts) == 1:
            self.lines[row] = before + text + after
            new = (row, col + len(text))
        else:
            self.lines[row] = before + parts[0]
            for i, part in enumerate(parts[1:-1], start=1):
                self.lines.insert(row + i, part)
            self.lines.insert(row + len(parts) - 1, parts[-1] + after)
            new = (row + len(parts) - 1, len(parts[-1]))
        self.set_pos(*new)
        return new
