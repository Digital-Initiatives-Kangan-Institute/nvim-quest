"""Local progress persistence (JSON save file)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Progress:
    completed: list[str] = field(default_factory=list)
    best_ranks: dict[str, str] = field(default_factory=dict)
    best_actions: dict[str, int] = field(default_factory=dict)
    unlocked_regions: list[str] = field(default_factory=list)

    def record(self, level_id: str, rank: str, actions: int) -> None:
        if level_id not in self.completed:
            self.completed.append(level_id)
        prev = self.best_ranks.get(level_id)
        from ..quest.scoring import RANK_ORDER

        if prev is None or RANK_ORDER.index(rank) > RANK_ORDER.index(prev):
            self.best_ranks[level_id] = rank
        if level_id not in self.best_actions or actions < self.best_actions[level_id]:
            self.best_actions[level_id] = actions

    def to_dict(self) -> dict:
        return {
            "completed": self.completed,
            "best_ranks": self.best_ranks,
            "best_actions": self.best_actions,
            "unlocked_regions": self.unlocked_regions,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Progress":
        return cls(
            completed=list(data.get("completed", [])),
            best_ranks=dict(data.get("best_ranks", {})),
            best_actions={k: int(v) for k, v in data.get("best_actions", {}).items()},
            unlocked_regions=list(data.get("unlocked_regions", ["Navigation"])),
        )


def default_save_path() -> Path:
    base = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    return Path(base) / "nvim-quest" / "save.json"


class ProgressStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_save_path()
        self.progress = self._load()

    def _load(self) -> Progress:
        try:
            with open(self.path) as f:
                return Progress.from_dict(json.load(f))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            return Progress(unlocked_regions=["Navigation"])

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.progress.to_dict(), f, indent=2)

    def record(self, level_id: str, rank: str, actions: int) -> None:
        self.progress.record(level_id, rank, actions)
        self.save()
