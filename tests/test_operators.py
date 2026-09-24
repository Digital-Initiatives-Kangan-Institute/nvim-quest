"""Unit tests for buffer mutation, edit operators, yank/put, and repeat."""

from nvim_quest.quest.evaluator import Evaluator
from nvim_quest.quest.models import Level
from nvim_quest.quest.scoring import MASTERY, rank_attempt
from nvim_quest.simulation.buffer import Buffer
from nvim_quest.simulation.state import VirtualEditor, _parse


def make(lines, row=0, col=0):
    return Buffer.from_lines(lines, row, col)


def ed(lines, row=0, col=0):
    return VirtualEditor(lines, (row, col))


# --- buffer mutation -------------------------------------------------------


def test_delete_char():
    b = make(["hello"], 0, 1)
    assert b.delete_char() == "e"
    assert b.lines == ["hllo"] and b.pos == (0, 1)
    assert b.delete_char(10) == "llo"
    assert b.lines == ["h"]


def test_delete_char_empty_line():
    b = make([""], 0, 0)
    assert b.delete_char() == ""


def test_delete_span_same_line():
    b = make(["hello"], 0, 0)
    assert b.delete_span((0, 1), (0, 4)) == "ell"
    assert b.lines == ["ho"] and b.pos == (0, 1)
    assert b.delete_span((0, 1), (0, 1)) == ""


def test_delete_span_multi_line_joins():
    b = make(["ab", "cd", "ef"], 0, 0)
    assert b.delete_span((0, 1), (2, 1)) == "b\ncd\ne"
    assert b.lines == ["af"] and b.pos == (0, 1)


def test_delete_lines_cursor_rule():
    b = make(["a", "  ind", "b"], 0, 0)
    assert b.delete_lines(0, 1) == ["a"]
    assert b.lines == ["  ind", "b"]
    assert b.pos == (0, 2)  # first non-blank


def test_delete_lines_never_removes_final():
    b = make(["only"], 0, 0)
    assert b.delete_lines(0, 5) == ["only"]
    assert b.lines == [""] and b.pos == (0, 0)


def test_insert_text():
    b = make(["ab"], 0, 0)
    assert b.insert_text(0, 1, "X") == (0, 2)
    assert b.lines == ["aXb"]
    b = make(["ab"], 0, 0)
    assert b.insert_text(0, 1, "X\nYZ") == (1, 2)
    assert b.lines == ["aX", "YZb"]


# --- parsing ---------------------------------------------------------------


def test_parse_operators():
    assert _parse("dw") == ("d", 1, "w")
    assert _parse("d2w") == ("d", 1, "2w")
    assert _parse("2dd") == ("d", 2, "line")
    assert _parse("dd") == ("d", 1, "line")
    assert _parse("ciw") == ("c", 1, "iw")
    assert _parse("yy") == ("y", 1, "line")
    assert _parse("x") == ("x", 1, "")
    assert _parse("p") == ("p", 1, "")
    assert _parse(".") == (".", 1, "")
    assert _parse("d") == ("d", 1, "")
    assert _parse("cc") == ("c", 1, "c")


# --- x ---------------------------------------------------------------------


def test_x_basic_and_register():
    e = ed(["abcd"], 0, 0)
    res = e.apply("x")
    assert res.key == "x" and res.family == "edit" and not res.invalid
    assert e.buf.lines == ["bcd"] and e.pos == (0, 0)
    assert e.unnamed is not None and e.unnamed.lines == ["a"]
    e.apply("2x")
    assert e.buf.lines == ["d"]


def test_x_empty_line_invalid():
    e = ed([""], 0, 0)
    assert e.apply("x").invalid is True


# --- delete ----------------------------------------------------------------


def test_dw_basic():
    e = ed(["map rope"], 0, 0)
    res = e.apply("dw")
    assert (res.key, res.family) == ("d", "edit")
    assert e.buf.lines == ["rope"] and e.pos == (0, 0)


def test_dw_last_word():
    e = ed(["hello"], 0, 0)
    assert e.apply("dw").invalid is False
    assert e.buf.lines == [""]


def test_dw_on_whitespace_invalid():
    e = ed(["   "], 0, 0)
    assert e.apply("dw").invalid is True


def test_counts_multiply():
    e = ed(["a b c"], 0, 0)
    e.apply("d2w")
    assert e.buf.lines == ["c"]
    e = ed(["a", "b", "c"], 0, 0)
    e.apply("2dd")
    assert e.buf.lines == ["c"]


def test_de_dollar_d0_db():
    e = ed(["map rope"], 0, 0)
    e.apply("de")
    assert e.buf.lines == [" rope"]
    e = ed(["abc"], 0, 1)
    e.apply("d$")
    assert e.buf.lines == ["a"]
    e = ed(["abc"], 0, 2)
    e.apply("d0")
    assert e.buf.lines == [""]
    e = ed(["map rope"], 0, 4)
    e.apply("db")
    # Backward-inclusive: deletes "map r", like real vim.
    assert e.buf.lines == ["ope"]


def test_dd_and_cursor():
    e = ed(["a", "  b", "c"], 1, 1)
    e.apply("dd")
    assert e.buf.lines == ["a", "c"] and e.pos == (1, 0)
    assert e.unnamed is not None and e.unnamed.linewise is True


def test_df_dt():
    e = ed(["a,b,c"], 0, 0)
    e.apply("df,")
    assert e.buf.lines == ["b,c"]
    e = ed(["ab,cd"], 0, 0)
    e.apply("dt,")
    assert e.buf.lines == ["b,cd"]


def test_bare_and_bad_operators_invalid():
    e = ed(["abc"], 0, 0)
    assert e.apply("d").invalid is True
    assert e.apply("dz").invalid is True
    assert e.apply("cc").invalid is True  # out of scope
    assert e.buf.lines == ["abc"]


def test_operator_respects_allowed_set():
    e = ed(["map rope"], 0, 0)
    assert e.apply("dw", {"h"}).invalid is True
    assert e.buf.lines == ["map rope"]


# --- change + insert -------------------------------------------------------


def test_cw_then_commit():
    e = ed(["old new"], 0, 0)
    res = e.apply("cw")
    assert res.enter_insert is True and e.awaiting_insert is True
    assert e.buf.lines == [" new"] and e.pos == (0, 0)
    assert e.commit_insert("young") is True
    assert e.buf.lines == ["young new"]
    assert e.awaiting_insert is False
    assert e.last_change is not None and e.last_change.inserted == "young"


def test_ciw_mid_word():
    e = ed(["hello"], 0, 2)
    e.apply("ciw")
    assert e.buf.lines == [""]
    e.commit_insert("hi")
    assert e.buf.lines == ["hi"]


def test_ciw_on_space_invalid():
    e = ed(["a b"], 0, 1)
    assert e.apply("ciw").invalid is True


def test_unfinished_change_auto_commits_empty():
    e = ed(["old new", "second"], 0, 0)
    e.apply("cw")
    assert e.buf.lines == [" new", "second"]
    res = e.apply("j")  # commits "" then moves
    assert res.invalid is False
    assert e.buf.lines == [" new", "second"] and e.pos == (1, 0)
    assert e.last_change is not None and e.last_change.inserted == ""


# --- yank / put ------------------------------------------------------------


def test_yy_put_linewise():
    e = ed(["one", "two"], 0, 0)
    res = e.apply("yy")
    assert res.key == "y" and not res.invalid
    assert e.buf.lines == ["one", "two"]
    e.apply("j")
    assert e.apply("p").invalid is False
    assert e.buf.lines == ["one", "two", "one"]
    assert e.pos == (2, 0)


def test_x_then_p_charwise():
    e = ed(["abc"], 0, 0)
    e.apply("x")
    e.apply("p")
    # Pastes after the cursor: b|a|c.
    assert e.buf.lines == ["bac"] and e.pos == (0, 1)


def test_put_empty_register_invalid():
    assert ed(["abc"], 0, 0).apply("p").invalid is True


def test_yy_empty_line_pastes_empty_line():
    e = ed([""], 0, 0)
    assert e.apply("yy").invalid is False
    assert e.apply("p").invalid is False
    assert e.buf.lines == ["", ""]


# --- repeat ----------------------------------------------------------------


def test_dot_with_no_history_invalid():
    assert ed(["abc"], 0, 0).apply(".").invalid is True


def test_dot_repeats_dw():
    e = ed(["one two", "three four"], 0, 0)
    e.apply("dw")
    e.apply("j")
    assert e.apply(".").invalid is False
    assert e.buf.lines == ["two", "four"]


def test_dot_repeats_x():
    e = ed(["abc"], 0, 0)
    e.apply("x")
    e.apply(".")
    assert e.buf.lines == ["c"]


def test_dot_repeats_change_with_text():
    e = ed(["old one", "old two"], 0, 0)
    e.apply("cw")
    e.commit_insert("new")
    e.apply("j")
    e.apply("b")  # repeat is position-dependent: back to word start
    e.apply(".")
    assert e.buf.lines == ["new one", "new two"]


def test_yank_does_not_disturb_repeat():
    e = ed(["a b", "c d"], 0, 0)
    e.apply("dw")
    e.apply("j")
    e.apply("yw")
    e.apply("k")
    e.apply(".")
    # Repeat runs `dw` on "b": last word of the line, so vim joins lines.
    assert e.buf.lines == ["c d"]


def test_dot_repeats_dd_and_put():
    e = ed(["a", "b", "c"], 0, 0)
    e.apply("dd")
    e.apply(".")
    assert e.buf.lines == ["c"]
    e = ed(["a", "b"], 0, 0)
    e.apply("yy")
    e.apply("j")
    e.apply("p")
    e.apply("k")
    e.apply(".")
    assert e.buf.lines == ["a", "b", "a", "a"]


# --- search resync ---------------------------------------------------------


def test_search_cleared_on_mutation():
    e = ed(["dog dog"], 0, 0)
    assert e.apply("/dog").invalid is False
    e.apply("x")
    assert e.apply("n").invalid is True


# --- evaluator text goal ---------------------------------------------------


def test_evaluator_text_goal_completion():
    lvl = Level(
        id="edit_test",
        title="Edit Test",
        lesson="Delete",
        start_text=["map rope"],
        start_cursor=(0, 0),
        targets=[],
        end_text=["rope"],
        allowed_commands=["d", "w", "h", "l"],
        reference_actions=1,
    )
    ev = Evaluator(lvl)
    hit, done = ev.submit("dw")
    assert (hit, done) == (True, True)
    assert rank_attempt(lvl, ev.stats) == MASTERY
