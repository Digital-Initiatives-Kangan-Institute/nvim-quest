"""Level solvability: reference solutions must complete every level.

Also asserts reference action counts match the YAML so Gold thresholds
stay honest, and that reference play earns Mastery.
"""

from pathlib import Path

import pytest

from nvim_quest.quest.evaluator import Evaluator
from nvim_quest.quest.loader import load_level
from nvim_quest.quest.scoring import MASTERY, rank_attempt

NAV = Path(__file__).parents[1] / "content" / "navigation"

# Reference solutions: plain keypresses (counts allowed but unused here,
# mirroring beginner play).
SOLUTIONS: dict[str, list[str]] = {
    "navigation_character_01": ["l"] * 6 + ["l"] * 7 + ["h"] * 13,
    "navigation_character_02": ["j", "j", "k", "j", "j"],
    "navigation_character_03": (
        ["j"] + ["l"] * 11 + ["j"] + ["h"] * 11 + ["j"] + ["l"] * 11
        + ["k"] * 3 + ["h"] * 11 + ["j"] * 2 + ["l"] * 11
    ),
    "navigation_word_01": ["w", "w", "e", "b", "b", "w", "w", "e"],
    "navigation_word_02": (
        ["w", "w", "w", "b", "b", "e", "e", "b", "b", "b"]
        + ["e"] * 5
    ),
    "navigation_word_03": (
        ["w", "e", "w", "e", "e", "e", "b", "b", "b", "b", "b", "e", "e", "e"]
    ),
    "navigation_word_04": (
        ["w", "w", "e", "e", "b", "b", "b", "w", "w", "w", "e", "e"]
        + ["b"] * 6 + ["e"] * 8
    ),
    "navigation_line_01": ["^", "$", "0", "$", "^"],
    "navigation_document_01": ["G", "gg"] + ["j"] * 12 + ["gg", "G"],
    "navigation_document_02": (
        ["j", "j", "^", "j", "j", "$", "gg", "G", "k", "k", "l", "0", "^"]
    ),
    "navigation_find_01": ["f,", "t,", "f,", "t,", "f,"],
    "navigation_find_02": (
        ["f(", "f,", "w", "t,", "w", "w", "w", "w", "f)"]
        + ["b"] * 9 + ["e"]
    ),
    "navigation_search_01": (
        ["/dragon", "n", "n", "N", "n", "n", "N", "N", "N"]
    ),
    "navigation_final_01": (
        ["j", "j", "j", "w", "e", "j", "j", "j", "j", "j",
         "^", "/dragon", "n", "G", "gg"]
    ),
}

EXPECTED_ORDER = [
    "navigation_character_01",
    "navigation_character_02",
    "navigation_character_03",
    "navigation_word_01",
    "navigation_word_02",
    "navigation_word_03",
    "navigation_word_04",
    "navigation_line_01",
    "navigation_document_01",
    "navigation_document_02",
    "navigation_find_01",
    "navigation_find_02",
    "navigation_search_01",
    "navigation_final_01",
]


def test_all_levels_present():
    ids = sorted(p.stem for p in NAV.glob("*.yaml"))
    assert ids == sorted(EXPECTED_ORDER)
    assert len(ids) == 14


@pytest.mark.parametrize("level_id", EXPECTED_ORDER)
def test_reference_solution_completes_with_mastery(level_id):
    level = load_level(NAV / f"{level_id}.yaml")
    solution = SOLUTIONS[level_id]
    assert len(solution) == level.reference_actions, (
        f"{level_id}: solution has {len(solution)} actions but "
        f"reference_actions={level.reference_actions}"
    )
    ev = Evaluator(level)
    for cmd in solution:
        hit, done = ev.submit(cmd)
    assert ev.stats.completed, (
        f"{level_id}: incomplete after reference solution "
        f"(visited {ev.stats.visited}/{len(level.targets)}, "
        f"invalid={ev.stats.invalid}, pos={ev.editor.pos})"
    )
    assert ev.stats.invalid == 0, f"{level_id}: reference had invalid commands"
    rank = rank_attempt(level, ev.stats)
    assert rank == MASTERY, f"{level_id}: reference ranked {rank}, want Mastery"
