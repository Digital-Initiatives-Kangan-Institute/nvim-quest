"""Forward/backward search session (/, n, N)."""

from __future__ import annotations


def find_matches(lines: list[str], term: str) -> list[tuple[int, int]]:
    """All (row, col) start positions of term, top-to-bottom, left-to-right."""
    matches: list[tuple[int, int]] = []
    if not term:
        return matches
    for row, line in enumerate(lines):
        start = 0
        while True:
            idx = line.find(term, start)
            if idx == -1:
                break
            matches.append((row, idx))
            start = idx + 1
    return matches


class SearchSession:
    def __init__(self, lines: list[str]) -> None:
        self.lines = lines
        self.term: str = ""
        self.matches: list[tuple[int, int]] = []
        self.index: int = -1  # index into matches of current position
        self.search_count: int = 0  # how many / searches started

    def search(self, term: str, cursor: tuple[int, int]) -> tuple[int, int] | None:
        """Start a search; jump to first match at-or-after cursor (wrap)."""
        self.term = term
        self.matches = find_matches(self.lines, term)
        self.search_count += 1
        if not self.matches:
            self.index = -1
            return None
        for i, m in enumerate(self.matches):
            if m >= cursor:
                self.index = i
                return m
        self.index = 0
        return self.matches[0]

    def next(self, cursor: tuple[int, int]) -> tuple[int, int] | None:
        """`n`: next match after cursor (wrap)."""
        if not self.matches:
            return None
        for i, m in enumerate(self.matches):
            if m > cursor:
                self.index = i
                return m
        self.index = 0
        return self.matches[0]

    def prev(self, cursor: tuple[int, int]) -> tuple[int, int] | None:
        """`N`: previous match before cursor (wrap)."""
        if not self.matches:
            return None
        for i in range(len(self.matches) - 1, -1, -1):
            if self.matches[i] < cursor:
                self.index = i
                return self.matches[i]
        self.index = len(self.matches) - 1
        return self.matches[-1]
