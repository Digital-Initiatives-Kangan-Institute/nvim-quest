"""Headless UI tests: playthroughs, menu refresh, keyboard navigation."""

import json

import pytest
from textual.widgets import Button, Static

from nvim_quest.progress.store import ProgressStore
from nvim_quest.ui.app import MenuScreen, NvimQuestApp, ResultsScreen
from nvim_quest.ui.quest_screen import QuestScreen, format_allowed_motions, key_to_char


def test_key_to_char_aliases():
    # Real-terminal key names must resolve to the typed characters.
    assert key_to_char("h") == "h"
    assert key_to_char("0") == "0"
    assert key_to_char("G") == "G"
    assert key_to_char("circumflex_accent") == "^"
    assert key_to_char("dollar_sign") == "$"
    assert key_to_char("comma") == ","
    assert key_to_char("left_parenthesis") == "("
    assert key_to_char("right_parenthesis") == ")"
    assert key_to_char("slash") == "/"
    assert key_to_char("question_mark") == "?"
    # Non-printable keys yield "".
    assert key_to_char("enter") == ""
    assert key_to_char("escape") == ""
    assert key_to_char("up") == ""
    assert key_to_char("ctrl+q") == ""


@pytest.mark.asyncio
async def test_play_level_one_end_to_end(tmp_path):
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:
        assert len(app.levels) == 34
        await pilot.click("#level-navigation_character_01")
        assert isinstance(app.screen, QuestScreen)
        for _ in range(6):
            await pilot.press("l")
        for _ in range(7):
            await pilot.press("l")
        for _ in range(13):
            await pilot.press("h")
        assert isinstance(app.screen, ResultsScreen)
        app.screen.query_one("#results-body", Static)  # results rendered
        saved = json.loads((tmp_path / "save.json").read_text())
        assert "navigation_character_01" in saved["completed"]
        assert saved["best_ranks"]["navigation_character_01"] == "Mastery"


@pytest.mark.asyncio
async def test_search_level_flow(tmp_path):
    """Level 13: open search with '/', submit term, ride n/N to completion."""
    from textual.widgets import Input

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_search_01")
        assert isinstance(app.screen, QuestScreen)
        await pilot.press("slash")
        await pilot.pause()
        search = app.screen.query_one("#search-input", Input)
        assert search.display and not search.disabled
        await pilot.press(*list("dragon"))
        await pilot.press("enter")
        await pilot.pause()
        scr = app.screen
        assert scr.ev.editor.pos == (0, 0)
        assert scr.ev.stats.visited == 1
        for key in ["n", "n", "N", "n", "n", "N", "N", "N"]:
            await pilot.press(key)
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["navigation_search_01"] == "Mastery"


@pytest.mark.asyncio
async def test_line_motions_with_real_key_names(tmp_path):
    """Archive Expedition via real terminal key names (^/$/0/gg).

    Regression test: ^ arrived as 'circumflex_accent' and $ as
    'dollar_sign', which the old handler ignored.
    """
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_document_02")
        assert isinstance(app.screen, QuestScreen)
        keys = ["j", "j", "circumflex_accent", "j", "j", "dollar_sign",
                "g", "g", "G", "dollar_sign", "2", "k", "0",
                "circumflex_accent"]
        for key in keys:
            await pilot.press(key)
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["navigation_document_02"] == "Mastery"


@pytest.mark.asyncio
async def test_find_level_with_real_key_names(tmp_path):
    """Hidden Rune: f<t> sequences where ',' arrives as 'comma'."""
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_find_01")
        assert isinstance(app.screen, QuestScreen)
        for key in ["f", "comma", "t", "comma", "f", "comma",
                    "t", "comma", "f", "comma"]:
            await pilot.press(key)
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["navigation_find_01"] == "Mastery"


@pytest.mark.asyncio
async def test_shift_does_not_cancel_pending_find(tmp_path):
    """Rune Hunter regression: pressing Shift (for '(') must not cancel f/t.

    Kitty-protocol terminals emit bare-modifier key events ('left_shift',
    'right_shift'); these must be ignored while a find is pending.
    """
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_find_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("f")
        assert scr.pending_find == "f"
        await pilot.press("left_shift")
        await pilot.pause()
        # Pending find survives the bare Shift press.
        assert scr.pending_find == "f"
        assert scr.ev.stats.actions == 0
        await pilot.press("left_parenthesis")
        await pilot.pause()
        assert scr.ev.editor.pos == (0, 10)
        assert scr.ev.stats.visited == 1


@pytest.mark.asyncio
async def test_shift_does_not_cancel_pending_g(tmp_path):
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_document_01")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("g")
        assert scr.pending_g is True
        await pilot.press("right_shift")
        await pilot.pause()
        assert scr.pending_g is True
        await pilot.press("g")
        await pilot.pause()
        assert scr.ev.editor.pos == (0, 0)
        assert scr.ev.stats.invalid == 0


@pytest.mark.asyncio
async def test_search_gated_when_not_in_lesson(tmp_path):
    """Word Explorer: '/' must not open search nor record a mistake."""
    from textual.widgets import Input

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_word_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("slash")
        await pilot.pause()
        search = scr.query_one("#search-input", Input)
        assert not search.display
        assert "Search isn't part of this lesson" in scr.message
        assert scr.ev.stats.actions == 0
        assert scr.ev.stats.invalid == 0
        # Lesson motions still work normally afterwards.
        await pilot.press("w")
        await pilot.pause()
        assert scr.ev.stats.actions == 1
        assert scr.ev.stats.invalid == 0


@pytest.mark.asyncio
async def test_counts_level_via_ui(tmp_path):
    """Long Strides: '7j' count prefix works through the real key path."""
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_counts_01")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("7", "j")
        await pilot.pause()
        assert scr.ev.editor.pos == (7, 0)
        assert scr.ev.stats.visited == 1
        await pilot.press("5", "k")
        await pilot.press("7", "j")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["navigation_counts_01"] == "Mastery"


@pytest.mark.asyncio
async def test_quest_shows_allowed_motions(tmp_path):
    """Quest screen lists allowed motions and newly introduced ones."""
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_character_01")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        allowed = str(scr.query_one("#quest-allowed", Static).content)
        assert "Allowed motions:" in allowed
        assert "]h[" in allowed and "]l[" in allowed
        # After using 'l', it shows as used (green) while 'h' stays new.
        await pilot.press("l")
        await pilot.pause()
        assert scr.ev.stats.keys_used == {"l"}
        assert "[green]l[/green]" in format_allowed_motions(
            scr.level, scr.ev.stats.keys_used)
        assert "[yellow]h[/yellow]" in format_allowed_motions(
            scr.level, scr.ev.stats.keys_used)


def test_format_allowed_motions():
    from nvim_quest.quest.models import Level

    lvl = Level(id="x", title="X", lesson="L",
                allowed_commands=["h", "l", "w"],
                introduced=["w"])
    fresh = format_allowed_motions(lvl, set())
    assert "[yellow]w[/yellow]" in fresh
    assert "[green]" not in fresh
    used = format_allowed_motions(lvl, {"h", "w"})
    assert "[green]h[/green]" in used
    assert "[green]w[/green]" in used  # used beats new
    assert " l " in used  # plain when neither used nor new


@pytest.mark.asyncio
async def test_silver_verdict_names_missing_key_and_overrun(tmp_path):
    """Archive Expedition without '0': 13×h instead → Silver + verdict.

    Skipping the now load-bearing '0' blows the action budget, so the
    verdict must name both the overrun and the missing key.
    """
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        await pilot.click("#level-navigation_document_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        mastery = str(scr.query_one("#quest-mastery", Static).content)
        assert "use 0 ^ $ gg G" in mastery
        keys = ["j", "j", "circumflex_accent", "j", "j", "dollar_sign",
                "g", "g", "G", "dollar_sign", "2", "k"]
        for key in keys:
            await pilot.press(key)
        assert scr.ev.editor.pos == (8, 13)
        for _ in range(13):
            await pilot.press("h")
        await pilot.press("circumflex_accent")
        assert isinstance(app.screen, ResultsScreen)
        body = str(app.screen.query_one("#results-body", Static).content)
        assert "Silver Rank" in body
        assert "24 actions (limit 12)" in body
        assert "never used 0" in body
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["navigation_document_02"] == "Silver"


@pytest.mark.asyncio
async def test_buffer_scroll_follows_cursor(tmp_path):
    """Grand Archive on a small screen: G scrolls down, gg scrolls back."""
    from textual.containers import VerticalScroll

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:  # default 80x24: 45 lines overflow
        for _ in range(19):  # last level button = Grand Archive
            await pilot.press("j")
        await pilot.press("l")
        await pilot.pause()
        assert isinstance(app.screen, QuestScreen)
        assert app.screen.level.id == "navigation_final_02"
        scroller = app.screen.query_one("#quest-buffer-scroll", VerticalScroll)
        assert scroller.scroll_y == 0
        await pilot.press("G")
        await pilot.pause()
        assert app.screen.ev.editor.pos == (44, 0)
        assert scroller.scroll_y > 0
        await pilot.press("g")
        await pilot.press("g")
        await pilot.pause()
        assert app.screen.ev.editor.pos == (0, 0)
        assert scroller.scroll_y == 0


@pytest.mark.asyncio
async def test_insert_flow_completes_text_goal(tmp_path):
    """cw → INSERT input → type → Enter commits and finishes the level."""
    from textual.widgets import Input

    from nvim_quest.quest.models import Level

    lvl = Level(
        id="edit_probe", title="Probe", lesson="Change",
        start_text=["map rope"], start_cursor=(0, 0),
        targets=[], end_text=["new rope"],
        allowed_commands=["c", "w", "h", "l"],
        reference_actions=1,
    )
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        app.push_screen(QuestScreen(lvl, store))
        await pilot.pause()
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("c")
        await pilot.pause()
        assert scr.op_prefix == "c"
        assert scr.ev.stats.actions == 0
        await pilot.press("w")
        await pilot.pause()
        assert scr.ev.editor.buf.lines == [" rope"]
        insert = scr.query_one("#insert-input", Input)
        assert insert.display and not insert.disabled
        await pilot.press(*list("new"))
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        body = str(app.screen.query_one("#results-body", Static).content)
        assert "Mastery Rank" in body
        diff = str(app.screen.query_one("#results-diff", Static).content)
        assert "- map rope" in diff and "+ new rope" in diff
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["edit_probe"] == "Mastery"


@pytest.mark.asyncio
async def test_operator_escape_cancels_without_action(tmp_path):
    """'c' then Escape: no action recorded, following 'w' is a plain motion."""
    from nvim_quest.quest.models import Level

    lvl = Level(
        id="edit_probe", title="Probe", lesson="Change",
        start_text=["map rope"], start_cursor=(0, 0),
        targets=[], end_text=["new rope"],
        allowed_commands=["c", "w", "h", "l"],
        reference_actions=1,
    )
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 70)) as pilot:
        app.push_screen(QuestScreen(lvl, store))
        await pilot.pause()
        scr = app.screen
        await pilot.press("c")
        await pilot.pause()
        assert scr.op_prefix == "c"
        await pilot.press("escape")
        await pilot.pause()
        assert scr.op_prefix == ""
        assert scr.ev.stats.actions == 0
        await pilot.press("w")
        await pilot.pause()
        assert scr.ev.editor.buf.lines == ["map rope"]
        assert scr.ev.editor.pos == (0, 4)
        assert scr.ev.stats.actions == 1
        assert scr.ev.stats.invalid == 0


@pytest.mark.asyncio
async def test_menu_tabs_and_mastery_gate(tmp_path):
    """Tabs per part; later parts locked until prior final is mastered."""
    from textual.widgets import Button, TabbedContent

    from nvim_quest.quest.models import Level
    from nvim_quest.ui.app import MenuScreen

    nav = Level(id="n1", title="Nav One", lesson="L", region="Navigation",
                order=1)
    edt = Level(id="e1", title="Edit One", lesson="M", region="Editing",
                order=2)
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:
        app.push_screen(MenuScreen(store, [("Navigation", [nav]),
                                           ("Editing", [edt])]))
        await pilot.pause()
        menu = app.screen
        assert isinstance(menu, MenuScreen)
        tabbed = menu.query_one(TabbedContent)
        assert tabbed.active == "tab-navigation"
        assert "Navigation: 0/1  ·  Editing: 0/1" in str(
            menu.query_one("#menu-progress", Static).content)
        # Editing locked: notice shown, buttons hidden.
        notice = str(menu.query_one("#notice-editing", Static).content)
        assert "LOCKED" in notice and "Nav One" in notice
        assert menu.query_one("#list-editing").display is False
        # j stays in the open tab; gt switches to the locked tab.
        await pilot.press("j")
        assert app.focused is menu.query_one("#quit-navigation", Button)
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        assert tabbed.active == "tab-editing"
        assert app.focused is menu.query_one("#quit-editing", Button)
        # gT switches back.
        await pilot.press("g")
        await pilot.press("T")
        await pilot.pause()
        assert tabbed.active == "tab-navigation"
        # Mastering the gatekeeper unlocks the next part on refresh.
        store.record("n1", "Mastery", 3)
        menu._refresh()
        await pilot.pause()
        assert menu.query_one("#list-editing").display is not False
        assert menu.query_one("#notice-editing").display is False
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        assert tabbed.active == "tab-editing"
        assert app.focused is menu.query_one("#level-e1", Button)
        await pilot.press("j")
        assert app.focused is menu.query_one("#quit-editing", Button)


def test_load_regions(tmp_path):
    from nvim_quest.quest.loader import content_dir, load_regions

    regions = load_regions(content_dir())
    assert [name for name, _ in regions] == ["Navigation", "Editing"]
    assert len(regions[0][1]) == 20
    assert len(regions[1][1]) == 14


@pytest.mark.asyncio
async def test_editing_level_playthrough(tmp_path):
    """First Cut via the menu: x-cuts complete a text goal end to end."""
    store = _store_with_editing_unlocked(tmp_path)
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 110)) as pilot:
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        await pilot.click("#level-editing_delete_01")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        assert scr.level.region == "Editing"
        for _ in range(6):
            await pilot.press("l")
        await pilot.press("x")
        for _ in range(10):
            await pilot.press("l")
        await pilot.press("x")
        assert isinstance(app.screen, ResultsScreen)
        body = str(app.screen.query_one("#results-body", Static).content)
        assert "Mastery Rank" in body
        diff = str(app.screen.query_one("#results-diff", Static).content)
        assert "the example code" in diff
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["editing_delete_01"] == "Mastery"


@pytest.mark.asyncio
async def test_ciw_flow_completes_inner_remedy(tmp_path):
    """Inner Remedy: c,i,w composes ciw (used to swallow the 'i')."""
    store = _store_with_editing_unlocked(tmp_path)
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 110)) as pilot:
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        await pilot.click("#level-editing_change_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        for k in ["c", "i", "w"]:
            await pilot.press(k)
        await pilot.pause()
        assert scr.ev.editor.buf.lines == ["fix  issuem"]
        await pilot.press(*list("the"))
        await pilot.press("enter")
        await pilot.pause()
        for k in ["w", "c", "i", "w"]:
            await pilot.press(k)
        await pilot.pause()
        assert scr.ev.editor.buf.lines == ["fix the "]
        await pilot.press(*list("issue"))
        await pilot.press("enter")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["editing_change_02"] == "Mastery"


@pytest.mark.asyncio
async def test_disallowed_insert_key_is_invalid(tmp_path):
    """Bare 'i' where insert isn't allowed records one invalid action."""
    store = _store_with_editing_unlocked(tmp_path)
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 110)) as pilot:
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        await pilot.click("#level-editing_change_02")
        scr = app.screen
        await pilot.press("i")
        await pilot.pause()
        assert scr.ev.stats.actions == 1
        assert scr.ev.stats.invalid == 1
        assert scr.ev.editor.in_live_insert is False


@pytest.mark.asyncio
async def test_replace_flow_completes_swap_letter(tmp_path):
    """Swap Letter via menu: r,i / r,o compose through pending_r."""
    store = _store_with_editing_unlocked(tmp_path)
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 120)) as pilot:
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        await pilot.click("#level-editing_change_04")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        for k in ["w", "l", "l", "r", "i", "w", "w", "l", "r", "o"]:
            await pilot.press(k)
        await pilot.pause()
        assert scr.ev.editor.buf.lines == ["the quick brown fox"]
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["editing_change_04"] == "Mastery"


@pytest.mark.asyncio
async def test_live_insert_both_directions(tmp_path):
    """Open Both Ways: O above, o below, Esc leaves insert each time."""
    from textual.widgets import Input

    store = _store_with_editing_unlocked(tmp_path)
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 120)) as pilot:
        await pilot.press("g")
        await pilot.press("t")
        await pilot.pause()
        await pilot.click("#level-editing_insert_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        await pilot.press("k")
        await pilot.press("O")
        await pilot.pause()
        assert scr.ev.editor.in_live_insert is True
        assert "-- INSERT --" in str(
            scr.query_one("#quest-status", Static).content)
        await pilot.press(*list("zero"))
        await pilot.press("escape")
        await pilot.pause()
        assert scr.ev.editor.buf.lines == ["zero", "first", "third"]
        assert scr.ev.editor.in_live_insert is False
        await pilot.press("j")
        await pilot.press("o")
        await pilot.pause()
        assert scr.ev.editor.in_live_insert is True
        await pilot.press(*list("second"))
        await pilot.press("escape")
        await pilot.pause()
        assert isinstance(app.screen, ResultsScreen)
        saved = json.loads((tmp_path / "save.json").read_text())
        assert saved["best_ranks"]["editing_insert_02"] == "Mastery"


def _store_with_editing_unlocked(tmp_path):
    """Fresh store with the Navigation final mastered (Editing playable)."""
    store = ProgressStore(path=tmp_path / "save.json")
    store.record("navigation_final_02", "Mastery", 20)
    return store


@pytest.mark.asyncio
async def test_demo_tracker_lists_missing_families(tmp_path):
    """Grand Archive: the mastery line names all six families up front."""
    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test(size=(100, 110)) as pilot:
        await pilot.click("#level-navigation_final_02")
        assert isinstance(app.screen, QuestScreen)
        scr = app.screen
        mastery = str(scr.query_one("#quest-mastery", Static).content)
        for fam in ["character", "word", "line", "document", "find",
                    "search"]:
            assert fam in mastery
        # Using word motions drops that family from the missing list.
        await pilot.press("w")
        await pilot.press("w")
        await pilot.pause()
        mastery = str(scr.query_one("#quest-mastery", Static).content)
        assert "word motions" not in mastery
        assert "find motions" in mastery
    """Menu shows the new rank immediately after returning from a level."""
    from textual.widgets import Button

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:
        btn = app.screen.query_one("#level-navigation_character_01", Button)
        assert "best: —" in str(btn.label)
        await pilot.click("#level-navigation_character_01")
        for _ in range(13):
            await pilot.press("l")
        for _ in range(13):
            await pilot.press("h")
        assert isinstance(app.screen, ResultsScreen)
        await pilot.click("#back")
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen)
        btn = app.screen.query_one("#level-navigation_character_01", Button)
        assert "best: Mastery" in str(btn.label)
        progress = app.screen.query_one("#menu-progress", Static)
        assert "1/20" in str(progress.content)
        # Pixel-level regression: the rank must actually render (buttons
        # used to keep their old width and crop the longer rank text).
        # Note: SVG encodes spaces as &#160;.
        svg = app.export_screenshot()
        assert "Mastery" in svg
        assert "(Character&#160;Motion)" in svg


@pytest.mark.asyncio
async def test_menu_keyboard_navigation(tmp_path):
    """Vim-only nav within the active tab: j/k move, l opens, gt tabs."""
    from textual.widgets import Button

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:  # default 80x24: menu overflows
        menu = app.screen
        assert isinstance(menu, MenuScreen)
        buttons = list(menu.query(Button))
        assert len(buttons) == 36  # 34 levels + per-tab Quit
        nav_buttons = buttons[:20]
        nav_quit = buttons[20]
        assert nav_quit.id == "quit-navigation"
        assert app.focused is nav_buttons[0]
        await pilot.press("j")
        assert app.focused is nav_buttons[1]
        await pilot.press("k")
        assert app.focused is nav_buttons[0]
        # Arrows are not vim motions: ignored.
        await pilot.press("down")
        await pilot.press("up")
        assert app.focused is nav_buttons[0]
        # Walk past the last level of the tab: lands on Quit (wraps in-tab).
        for _ in range(20):
            await pilot.press("j")
        assert app.focused is nav_quit
        from textual.containers import VerticalScroll

        scroller = menu.query_one("#list-navigation", VerticalScroll)
        assert scroller.scroll_y > 0
        # Quit must actually render (it used to sit off-screen, unreachable).
        assert "Quit" in app.export_screenshot()
        quit_region = menu.query_one("#quit-navigation", Button).region
        assert quit_region.y + quit_region.height <= menu.size.height
        # One more j wraps back to the top of the tab (never into Editing).
        await pilot.press("j")
        assert app.focused is nav_buttons[0]
        # Open the second level with 'l'.
        await pilot.press("j")
        await pilot.press("l")
        await pilot.pause()
        assert isinstance(app.screen, QuestScreen)
        assert app.screen.level.id == "navigation_character_02"


def test_main_disables_mouse(monkeypatch):
    """The game is keyboard-only: terminal mouse reporting stays off."""
    from nvim_quest import __main__ as main_module
    from nvim_quest.ui.app import NvimQuestApp

    calls: dict = {}

    def fake_run(self, **kwargs):
        calls.update(kwargs)

    monkeypatch.setattr(NvimQuestApp, "run", fake_run)
    main_module.main()
    assert calls.get("mouse") is False
