"""Textual app: main menu, results, progress."""

from __future__ import annotations

import time

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from ..progress.store import ProgressStore
from ..quest.evaluator import AttemptStats
from ..quest.loader import content_dir, load_levels
from ..quest.models import Level
from ..quest.scoring import RANK_ORDER
from ..simulation.state import CommandResult
from .quest_screen import QuestScreen


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


class MenuScreen(Screen):
    BINDINGS = [("q", "quit_app", "Quit")]

    def __init__(self, store: ProgressStore, levels: list[Level]) -> None:
        super().__init__()
        self.store = store
        self.levels = levels

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu"):
            yield Static("[bold]NeoVim Quest[/bold]\n[dim]Learn real Neovim workflows by playing.[/dim]")
            yield Static(id="menu-progress")
            yield Static("[bold]Lessons — Navigation[/bold]")
            for lvl in self.levels:
                yield Button(self._label(lvl), id=f"level-{lvl.id}")
            yield Button("Quit", id="quit", variant="error")
        yield Footer()

    def _label(self, lvl: Level) -> str:
        rank = self.store.progress.best_ranks.get(lvl.id, "—")
        return f"{lvl.title}  [{lvl.lesson}]  best: {rank}"

    def _refresh(self) -> None:
        for lvl in self.levels:
            self.query_one(f"#level-{lvl.id}", Button).label = self._label(lvl)
        done = len(self.store.progress.completed)
        total = len(self.levels)
        self.query_one("#menu-progress", Static).update(
            f"Progress: {done}/{total} levels complete"
        )

    def on_mount(self) -> None:
        self._refresh()
        buttons = list(self.query(Button))
        if buttons:
            self.set_focus(buttons[0])

    def on_screen_resume(self) -> None:
        # Returning from a quest: ranks/progress may have changed.
        self._refresh()

    # -- keyboard navigation (arrows + vim) ------------------------------

    def _buttons(self) -> list[Button]:
        return list(self.query(Button))

    def _move_focus(self, direction: int) -> None:
        buttons = self._buttons()
        if not buttons:
            return
        try:
            index = buttons.index(self.focused)
        except ValueError:
            index = 0 if direction > 0 else len(buttons) - 1
            self.set_focus(buttons[index])
            return
        self.set_focus(buttons[(index + direction) % len(buttons)])

    def _open_focused(self) -> None:
        focused = self.focused
        if not isinstance(focused, Button):
            return
        btn = focused.id or ""
        if btn == "quit":
            self.app.exit()
        elif btn.startswith("level-"):
            level_id = btn[len("level-"):]
            level = next(l for l in self.levels if l.id == level_id)
            self.app.push_screen(QuestScreen(level, self.store))

    async def on_key(self, event) -> None:
        key = event.key
        if key in ("down", "j"):
            self._move_focus(1)
            event.prevent_default()
        elif key in ("up", "k"):
            self._move_focus(-1)
            event.prevent_default()
        elif key in ("l", "right"):
            self._open_focused()
            event.prevent_default()
        # "enter" activates the focused button natively; "q" quits via binding.

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id or ""
        if btn == "quit":
            self.app.exit()
        elif btn.startswith("level-"):
            level_id = btn[len("level-"):]
            level = next(l for l in self.levels if l.id == level_id)
            self.app.push_screen(QuestScreen(level, self.store))

    def action_quit_app(self) -> None:
        self.app.exit()


class ResultsScreen(Screen):
    def __init__(self, level: Level, stats: AttemptStats, rank: str,
                 elapsed: float, history: list[CommandResult]) -> None:
        super().__init__()
        self.level = level
        self.stats = stats
        self.rank = rank
        self.elapsed = elapsed
        self.history = history

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("[bold]Quest Complete[/bold]")
            yield Static(id="results-body")
            yield Button("Back to Lessons", id="back", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        used = " ".join(r.command for r in self.history if not r.invalid)
        fams = ", ".join(sorted(self.stats.families_used)) or "—"
        self.query_one("#results-body", Static).update(
            f"[bold]{self.level.title}[/bold] — [yellow]{self.rank} Rank[/yellow]\n\n"
            f"Time: {_fmt_time(self.elapsed)}\n"
            f"Actions: {self.stats.actions} (reference: {self.level.reference_actions})\n"
            f"Mistakes: {self.stats.invalid}\n"
            f"Hints used: {self.stats.hints_used}\n"
            f"Motion families: {fams}\n\n"
            f"[dim]You used:[/dim] {used}"
        )

    @on(Button.Pressed, "#back")
    def _back(self) -> None:
        # Pop results + quest screen, then refresh menu progress.
        self.app.pop_screen()
        self.app.pop_screen()


class NvimQuestApp(App):
    TITLE = "NeoVim Quest"
    CSS = """
    #menu { padding: 1 2; }
    #menu Button { margin-top: 0; }
    #quest-title { padding: 0 1; }
    #quest-objective { padding: 0 1; color: #9ecbff; }
    #quest-targets { padding: 0 1; }
    #quest-buffer { padding: 1 2; border: solid #444; }
    #quest-status { padding: 0 1; }
    """

    def __init__(self, store: ProgressStore | None = None) -> None:
        super().__init__()
        self.store = store or ProgressStore()
        self.levels = load_levels(content_dir() / "navigation")

    def on_mount(self) -> None:
        self.push_screen(MenuScreen(self.store, self.levels))
