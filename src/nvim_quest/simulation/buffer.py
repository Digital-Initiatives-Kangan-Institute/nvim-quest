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
