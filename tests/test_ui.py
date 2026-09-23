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
        assert len(app.levels) == 20
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
async def test_menu_refreshes_ranks_without_restart(tmp_path):
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
    """Vim-only nav: j/k move focus (scrolling follows), l opens."""
    from textual.widgets import Button

    store = ProgressStore(path=tmp_path / "save.json")
    app = NvimQuestApp(store=store)
    async with app.run_test() as pilot:  # default 80x24: menu overflows
        menu = app.screen
        assert isinstance(menu, MenuScreen)
        buttons = list(menu.query(Button))
        assert len(buttons) == 21  # 20 levels + quit
        assert app.focused is buttons[0]
        await pilot.press("j")
        assert app.focused is buttons[1]
        await pilot.press("k")
        assert app.focused is buttons[0]
        # Arrows are not vim motions: ignored.
        await pilot.press("down")
        await pilot.press("up")
        assert app.focused is buttons[0]
        # Walk to the bottom: focus tracks and the view scrolls with it.
        for _ in range(len(buttons) - 1):
            await pilot.press("j")
        assert app.focused is buttons[-1]
        from textual.containers import VerticalScroll

        scroller = menu.query_one("#level-list", VerticalScroll)
        assert scroller.scroll_y > 0
        # Walk back to the second button and open it with 'l'.
        for _ in range(len(buttons) - 2):
            await pilot.press("k")
        assert app.focused is buttons[1]
        await pilot.press("l")
        await pilot.pause()
        assert isinstance(app.screen, QuestScreen)
        assert app.screen.level.id == "navigation_character_02"
