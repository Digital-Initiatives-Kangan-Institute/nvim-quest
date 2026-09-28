"""Level solvability: reference solutions must complete every level.

Also asserts reference action counts match the YAML so Gold thresholds
stay honest, and that reference play earns Mastery.
"""

import pytest

from nvim_quest.quest.evaluator import Evaluator
from nvim_quest.quest.loader import content_dir, load_level
from nvim_quest.quest.scoring import MASTERY, rank_attempt

NAV = content_dir() / "navigation"
EDIT = content_dir() / "editing"

# Step = command string (one action), ("type", text) for widget insert
# commits, or ("live", text) for live-typed insert sessions (both part of
# the surrounding change/entry action, not new actions).
Step = str | tuple[str, str]

# Reference solutions: plain keypresses (counts allowed but unused here,
# mirroring beginner play).
SOLUTIONS: dict[str, list[Step]] = {
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
    "navigation_counts_01": ["7j", "5k", "7j"],
    "navigation_line_01": ["^", "$", "0", "$", "^"],
    "navigation_document_01": ["G", "gg"] + ["j"] * 12 + ["gg", "G"],
    "navigation_document_02": (
        ["j", "j", "^", "j", "j", "$", "gg", "G", "$", "2k", "0", "^"]
    ),
    "navigation_document_03": (
        ["4j", "^", "4j", "$", "gg", "G", "2k", "^", "k", "$"]
    ),
    "navigation_document_04": (
        ["4j", "^", "3j", "$", "0", "3j", "2k", "4j", "^"]
    ),
    "navigation_find_01": ["f,", "t,", "f,", "t,", "f,"],
    "navigation_find_02": (
        ["f(", "f,", "w", "t,", "w", "w", "w", "w", "f)"]
        + ["b"] * 9 + ["e"]
    ),
    "navigation_search_01": (
        ["/dragon", "n", "n", "N", "n", "n", "N", "N", "N"]
    ),
    "navigation_search_02": (
        ["/ember", "/frost", "n", "/ember", "/ember", "N", "N",
         "/frost", "n", "n", "/ember", "n"]
    ),
    "navigation_search_03": (
        ["/silver", "n", "e", "e", "n", "w", "N", "N", "N", "e", "e"]
    ),
    "navigation_final_01": (
        ["j", "j", "j", "w", "e", "j", "j", "j", "j", "j",
         "^", "/dragon", "n", "G", "gg"]
    ),
    "navigation_final_02": (
        ["4j", "w", "w", "e", "e", "e", "j", "0", "f:", "9j", "h",
         "4j", "^", "2j", "$", "/sigil", "n", "n", "G", "gg"]
    ),
}

EDIT_SOLUTIONS: dict[str, list[Step]] = {
    "editing_delete_01": ["l"] * 6 + ["x"] + ["l"] * 10 + ["x"],
    "editing_delete_02": ["w", "dw", "w", "dw"],
    "editing_delete_03": ["j", "dd", "dd", "j", "dd"],
    "editing_change_01": ["w", "cw", ("type", "new")],
    "editing_change_02": ["ciw", ("type", "the"), "w", "ciw",
                          ("type", "issue")],
    "editing_change_03": ["cc", ("type", "Done: rewritten"), "j", "j",
                          "cc", ("type", "Done: this too")],
    "editing_change_04": ["w", "l", "l", "ri", "w", "w", "l", "ro"],
    "editing_yank_01": ["yy", "p"],
    "editing_yank_02": ["dd", "j", "p"],
    "editing_repeat_01": ["cw", ("type", "new"), "j", "b", ".",
                          "j", "b", "."],
    "editing_insert_01": ["a", ("live", " gate")],
    "editing_insert_02": ["k", "O", ("live", "zero"), "j", "o",
                          ("live", "second")],
    "editing_insert_03": ["i", ("live", "o")],
    "editing_join_01": ["k", "k", "J"],
}

EDIT_ORDER = [
    "editing_delete_01",
    "editing_delete_02",
    "editing_delete_03",
    "editing_change_01",
    "editing_change_02",
    "editing_change_03",
    "editing_change_04",
    "editing_yank_01",
    "editing_yank_02",
    "editing_repeat_01",
    "editing_insert_01",
    "editing_insert_02",
    "editing_insert_03",
    "editing_join_01",
]

EXPECTED_ORDER = [
    "navigation_character_01",
    "navigation_character_02",
    "navigation_character_03",
    "navigation_word_01",
    "navigation_word_02",
    "navigation_word_03",
    "navigation_word_04",
    "navigation_counts_01",
    "navigation_line_01",
    "navigation_document_01",
    "navigation_document_02",
    "navigation_document_03",
    "navigation_document_04",
    "navigation_find_01",
    "navigation_find_02",
    "navigation_search_01",
    "navigation_search_02",
    "navigation_search_03",
    "navigation_final_01",
    "navigation_final_02",
]


def test_all_levels_present():
    ids = sorted(p.stem for p in NAV.glob("*.yaml"))
    assert ids == sorted(EXPECTED_ORDER)
    assert len(ids) == 20
    edit_ids = sorted(p.stem for p in EDIT.glob("*.yaml"))
    assert edit_ids == sorted(EDIT_ORDER)
    assert len(edit_ids) == 14


def test_levels_load_in_pedagogical_order():
    from nvim_quest.quest.loader import load_levels, load_regions

    levels = load_levels(NAV)
    assert [l.id for l in levels] == EXPECTED_ORDER
    levels = load_levels(EDIT)
    assert [l.id for l in levels] == EDIT_ORDER
    regions = load_regions()
    assert [name for name, _ in regions] == ["Navigation", "Editing"]
    assert [l.id for _, lvls in regions for l in lvls] == (
        EXPECTED_ORDER + EDIT_ORDER
    )


def _run_solution(directory, level_id: str, solution: list[Step]) -> None:
    level = load_level(directory / f"{level_id}.yaml")
    actions = sum(1 for step in solution if isinstance(step, str))
    assert actions == level.reference_actions, (
        f"{level_id}: solution has {actions} actions but "
        f"reference_actions={level.reference_actions}"
    )
    ev = Evaluator(level)
    for step in solution:
        if isinstance(step, tuple):
            kind, text = step
            if kind == "type":
                # Widget insert commit: advances state without a new action,
                # exactly like the quest screen (which calls check_progress).
                assert ev.editor.commit_insert(text) is True
            else:
                # Live-typed session: type the whole run, leave, re-check.
                assert ev.editor.in_live_insert
                assert ev.editor.insert_text_at_cursor(text) is True
                assert ev.editor.leave_insert() is True
            ev.check_progress()
        else:
            hit, done = ev.submit(step)
    assert ev.stats.completed, (
        f"{level_id}: incomplete after reference solution "
        f"(visited {ev.stats.visited}/{len(level.targets)}, "
        f"end={ev.editor.buf.lines!r}, "
        f"invalid={ev.stats.invalid}, pos={ev.editor.pos})"
    )
    assert ev.stats.invalid == 0, f"{level_id}: reference had invalid commands"
    rank = rank_attempt(level, ev.stats)
    assert rank == MASTERY, f"{level_id}: reference ranked {rank}, want Mastery"


@pytest.mark.parametrize("level_id", EXPECTED_ORDER)
def test_reference_solution_completes_with_mastery(level_id):
    _run_solution(NAV, level_id, SOLUTIONS[level_id])


@pytest.mark.parametrize("level_id", EDIT_ORDER)
def test_editing_reference_solution_completes_with_mastery(level_id):
    _run_solution(EDIT, level_id, EDIT_SOLUTIONS[level_id])
