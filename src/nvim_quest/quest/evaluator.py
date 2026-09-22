"""Evaluation: track ordered target visits during a level attempt."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..simulation.state import VirtualEditor
from .models import Level


@dataclass
class AttemptStats:
    actions: int = 0
    invalid: int = 0
    hints_used: int = 0
    families_used: set[str] = field(default_factory=set)
    keys_used: set[str] = field(default_factory=set)
    visited: int = 0  # number of targets visited in order
    completed: bool = False
    search_count: int = 0


class Evaluator:
    """Feeds commands through the editor and checks target order."""

    def __init__(self, level: Level) -> None:
        self.level = level
        self.editor = VirtualEditor(
            lines=list(level.start_text), start=level.start_cursor
        )
        self.stats = AttemptStats()
        self._next_target = 0
        self._check_start_position()

    def _check_start_position(self) -> None:
        # If the cursor starts on the first target, that counts as visited
        # only after an explicit action; do not auto-visit. Standard: no.
        pass

    @property
    def current_target_index(self) -> int:
        return self._next_target

    def pending_targets(self) -> int:
        return len(self.level.targets) - self._next_target

    def submit(self, command: str) -> tuple[bool, bool]:
        """Apply a command.

        Returns (target_hit, level_complete).
        """
        res = self.editor.apply(command, self.level.allowed_set)
        self.stats.actions += 1
        if res.invalid:
            self.stats.invalid += 1
        else:
            self.stats.families_used.add(res.family)
            self.stats.keys_used.add(res.key)
        if res.key == "/":
            self.stats.search_count = self.editor.search.search_count

        hit = False
        if self._next_target < len(self.level.targets):
            target = self.level.targets[self._next_target]
            if self.editor.pos == target.pos:
                hit = True
                self._next_target += 1
                self.stats.visited = self._next_target
        if self._next_target >= len(self.level.targets):
            self.stats.completed = True
        return (hit, self.stats.completed)

    def use_hint(self) -> None:
        self.stats.hints_used += 1
