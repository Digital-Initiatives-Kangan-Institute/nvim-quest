"""Load Level definitions from YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Level, level_from_dict


def load_level(path: str | Path) -> Level:
    with open(path) as f:
        data = yaml.safe_load(f)
    return level_from_dict(data)


def load_levels(directory: str | Path) -> list[Level]:
    levels: list[Level] = []
    for path in sorted(Path(directory).glob("*.yaml")):
        levels.append(load_level(path))
    # Pedagogical order, not filename order.
    levels.sort(key=lambda l: (l.order, l.id))
    return levels


def content_dir() -> Path:
    """Content root, shipped inside the package.

    Works for editable checkouts and regular installs alike, since the
    YAML files are declared as package data.
    """
    here = Path(__file__).resolve()
    candidate = here.parents[1] / "content"  # src/nvim_quest/content
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError("nvim_quest content directory not found")
