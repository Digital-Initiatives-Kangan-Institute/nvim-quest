"""Quest level data model."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Target:
    row: int
    col: int
    label: str = ""

    @property
    def pos(self) -> tuple[int, int]:
        return (self.row, self.col)


@dataclass
class MasteryRule:
    required_families: list[str] = field(default_factory=list)
    required_keys: list[str] = field(default_factory=list)
    min_families: int = 0  # alternative: at least N distinct families used
    max_actions: int = 0  # 0 = fall back to reference_actions
    single_search: bool = False  # mastery needs exactly one / search


@dataclass
class Level:
    id: str
    title: str
    lesson: str
    order: int = 0
    region: str = "Navigation"
    narrative: str = ""
    objective: str = ""
    start_text: list[str] = field(default_factory=list)
    start_cursor: tuple[int, int] = (0, 0)
    targets: list[Target] = field(default_factory=list)
    allowed_commands: list[str] = field(default_factory=list)
    introduced: list[str] = field(default_factory=list)
    hints: list[str] = field(default_factory=list)
    reference_actions: int = 0
    mastery: MasteryRule = field(default_factory=MasteryRule)

    @property
    def allowed_set(self) -> set[str]:
        return set(self.allowed_commands)


def level_from_dict(data: dict) -> Level:
    targets = [
        Target(row=t["row"], col=t["col"], label=t.get("label", ""))
        for t in data.get("targets", [])
    ]
    m = data.get("mastery", {})
    mastery = MasteryRule(
        required_families=list(m.get("required_families", [])),
        required_keys=list(m.get("required_keys", [])),
        min_families=int(m.get("min_families", 0)),
        max_actions=int(m.get("max_actions", 0)),
        single_search=bool(m.get("single_search", False)),
    )
    sc = data.get("start_cursor", [0, 0])
    return Level(
        id=data["id"],
        title=data.get("title", data["id"]),
        lesson=data.get("lesson", ""),
        order=int(data.get("order", 0)),
        region=data.get("region", "Navigation"),
        narrative=data.get("narrative", ""),
        objective=data.get("objective", ""),
        start_text=list(data.get("start_text", [])),
        start_cursor=(int(sc[0]), int(sc[1])),
        targets=targets,
        allowed_commands=list(data.get("allowed_commands", [])),
        introduced=list(data.get("introduced", [])),
        hints=list(data.get("hints", [])),
        reference_actions=int(data.get("reference_actions", 0)),
        mastery=mastery,
    )
