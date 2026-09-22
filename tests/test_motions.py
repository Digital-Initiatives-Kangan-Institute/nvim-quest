"""Unit tests for character/word/line/document/find motions."""

from nvim_quest.simulation.buffer import Buffer
from nvim_quest.simulation import motions


def make(lines, row=0, col=0):
    return Buffer.from_lines(lines, row, col)


def test_h_l_clamp_at_edges():
    b = make(["abc"], 0, 0)
    assert motions.move_h(b) is False
    assert b.pos == (0, 0)
    assert motions.move_l(b) is True
    assert b.pos == (0, 1)
    b.set_pos(0, 2)
    assert motions.move_l(b) is False


def test_j_k_preserve_column():
    b = make(["hello", "hi", "hello again"], 0, 4)
    assert motions.move_j(b) is True
    assert b.pos == (1, 1)  # clamped to short line
    assert motions.move_j(b) is True
    assert b.pos == (2, 4)  # preferred column restored
    assert motions.move_k(b) is True
    assert b.pos == (1, 1)
    assert motions.move_k(b) is True
    assert b.pos == (0, 4)


def test_j_k_counts():
    b = make(["a", "b", "c", "d"], 0, 0)
    assert motions.move_j(b, 3) is True
    assert b.pos == (3, 0)
    assert motions.move_k(b, 2) is True
    assert b.pos == (1, 0)


def test_w_basic():
    b = make(["map rope lantern"], 0, 0)
    motions.move_w(b)
    assert b.pos == (0, 4)  # start of rope
    motions.move_w(b)
    assert b.pos == (0, 9)  # start of lantern


def test_w_skips_punctuation_run():
    b = make(["a, b"], 0, 0)
    motions.move_w(b)
    assert b.pos == (0, 1)  # ',' is its own word
    motions.move_w(b)
    assert b.pos == (0, 3)  # 'b'


def test_e_basic():
    b = make(["map rope"], 0, 0)
    motions.move_e(b)
    assert b.pos == (0, 2)  # end of map
    motions.move_e(b)
    assert b.pos == (0, 7)  # end of rope


def test_e_from_word_end_goes_to_next():
    b = make(["map rope"], 0, 2)
    motions.move_e(b)
    assert b.pos == (0, 7)


def test_b_basic():
    b = make(["map rope lantern"], 0, 15)
    motions.move_b(b)
    assert b.pos == (0, 9)  # start of lantern
    motions.move_b(b)
    assert b.pos == (0, 4)  # start of rope


def test_b_at_buffer_start_no_move():
    b = make(["map"], 0, 0)
    assert motions.move_b(b) is False


def test_w_crosses_lines():
    b = make(["map", "rope"], 0, 0)
    motions.move_w(b)
    assert b.pos == (1, 0)


def test_word_counts():
    b = make(["a b c d"], 0, 0)
    motions.move_w(b, 3)
    assert b.pos == (0, 6)  # start of d


def test_line_motions_contrast():
    b = make(["   open_gate()"], 0, 5)
    motions.move_dollar(b)
    assert b.pos == (0, 13)
    motions.move_0(b)
    assert b.pos == (0, 0)
    motions.move_caret(b)
    assert b.pos == (0, 3)


def test_caret_blank_line():
    b = make(["", "hi"], 0, 0)
    assert motions.move_caret(b) is False
    assert b.pos == (0, 0)


def test_gg_G():
    lines = ["first", "middle", "last"]
    b = make(lines, 1, 2)
    motions.move_gg(b)
    assert b.pos == (0, 0)
    motions.move_G(b)
    assert b.pos == (2, 0)


def test_find_f_and_t():
    b = make(["iron, silver, amber"], 0, 0)
    assert motions.move_f(b, ",") is True
    assert b.pos == (0, 4)  # on first comma
    # t from before second comma lands just before it
    assert motions.move_t(b, ",") is True
    assert b.pos == (0, 11)  # char before second comma at 12
    assert motions.move_f(b, ",") is True
    assert b.pos == (0, 12)


def test_find_miss_is_noop():
    b = make(["abc"], 0, 0)
    assert motions.move_f(b, "z") is False
    assert motions.move_t(b, "z") is False
    assert b.pos == (0, 0)


def test_t_adjacent_no_room():
    b = make(["ab"], 0, 0)
    # 'b' is immediately next; t stops before it which is current pos
    assert motions.move_t(b, "b") is False
