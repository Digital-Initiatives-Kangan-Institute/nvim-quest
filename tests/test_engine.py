"""Tests for search sessions, command parsing, evaluator, and scoring."""

from nvim_quest.quest.evaluator import Evaluator
from nvim_quest.quest.models import Level, MasteryRule, Target
from nvim_quest.quest.scoring import GOLD, MASTERY, BRONZE, SILVER, LOCKED, rank_attempt
from nvim_quest.simulation.search import SearchSession, find_matches
from nvim_quest.simulation.state import VirtualEditor, _parse


def test_parse():
    assert _parse("w") == ("w", 1, "")
    assert _parse("3j") == ("j", 3, "")
    assert _parse("f,") == ("f", 1, ",")
    assert _parse("/dragon") == ("/", 1, "dragon")
    assert _parse("gg") == ("gg", 1, "")
    assert _parse("xyz") == ("", 1, "")


def test_find_matches_order():
    lines = ["dragon sword", "magic", "dragon shield"]
    assert find_matches(lines, "dragon") == [(0, 0), (2, 0)]


def test_search_wrap_and_n_N():
    s = SearchSession(["dragon a", "b dragon"])
    assert s.search("dragon", (0, 0)) == (0, 0)
    assert s.next((0, 0)) == (1, 2)
    assert s.next((1, 2)) == (0, 0)  # wraps
    assert s.prev((0, 0)) == (1, 2)  # wraps backward
    assert s.search("zzz", (0, 0)) is None


def test_editor_allowed_set_and_invalid():
    ed = VirtualEditor(["abc"], (0, 0))
    res = ed.apply("w", {"h", "l"})
    assert res.invalid is True
    assert ed.pos == (0, 0)
    res = ed.apply("l", {"h", "l"})
    assert res.invalid is False
    assert ed.pos == (0, 1)


def test_editor_noop_is_invalid():
    ed = VirtualEditor(["abc"], (0, 0))
    res = ed.apply("h")
    assert res.invalid is True


def make_level(**kw):
    base = dict(
        id="test",
        title="Test",
        lesson="L",
        start_text=["map rope lantern"],
        start_cursor=(0, 0),
        targets=[Target(0, 4, "rope"), Target(0, 9, "lantern")],
        allowed_commands=["w", "b", "h", "l"],
        reference_actions=2,
    )
    base.update(kw)
    return Level(**base)


def test_evaluator_order_matters():
    ev = Evaluator(make_level())
    hit, done = ev.submit("w")
    assert (hit, done) == (True, False)
    hit, done = ev.submit("w")
    assert (hit, done) == (True, True)
    assert ev.stats.invalid == 0


def test_evaluator_wrong_order_does_not_advance():
    # b from start is a no-op -> invalid, no target hit
    ev = Evaluator(make_level())
    hit, done = ev.submit("b")
    assert hit is False and done is False
    assert ev.stats.invalid == 1


def test_rank_progression():
    lvl = make_level(mastery=MasteryRule(required_families=["word"]))
    from nvim_quest.quest.evaluator import AttemptStats

    s = AttemptStats(actions=5, invalid=0, completed=True, families_used={"word"})
    assert rank_attempt(lvl, s) == SILVER  # over reference (2) -> silver only
    s = AttemptStats(actions=2, invalid=1, completed=True, families_used={"word"})
    assert rank_attempt(lvl, s) == BRONZE  # invalid blocks silver
    s = AttemptStats(actions=2, invalid=0, completed=True, families_used={"character"})
    assert rank_attempt(lvl, s) == GOLD  # families only gate mastery
    s = AttemptStats(actions=2, invalid=0, completed=True, families_used={"word"})
    assert rank_attempt(lvl, s) == MASTERY
    s = AttemptStats(actions=2, invalid=0, completed=False)
    assert rank_attempt(lvl, s) == LOCKED
    # hints block mastery but keep gold
    s = AttemptStats(actions=2, invalid=0, completed=True,
                     families_used={"word"}, hints_used=1)
    assert rank_attempt(lvl, s) == GOLD


def test_rank_silver_only():
    lvl = make_level(reference_actions=2)
    from nvim_quest.quest.evaluator import AttemptStats

    s = AttemptStats(actions=4, invalid=0, completed=True, families_used={"word"})
    assert rank_attempt(lvl, s) == SILVER
