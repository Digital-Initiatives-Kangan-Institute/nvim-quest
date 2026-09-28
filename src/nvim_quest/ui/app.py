"""Textual app: main menu, results, progress."""

from __future__ import annotations

import time

from textual import on
from textual.app import App, ComposeResult
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static, TabbedContent, TabPane

from ..progress.store import ProgressStore
from ..quest.evaluator import AttemptStats
from ..quest.loader import load_regions
from ..quest.models import Level
from ..quest.scoring import MASTERY, RANK_ORDER, mastery_gaps
from ..simulation.state import CommandResult
from .quest_screen import QuestScreen


def _fmt_time(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def diff_text(start: list[str], end: list[str] | None, shown: int = 4):
    """Index diff of start vs end lines as a Rich Text (markup-safe)."""
    from rich.text import Text

    out = Text()
    if end is None or end == start:
        out.append("No text changes.")
        return out
    pairs: list[tuple[str | None, str | None]] = []
    for i in range(max(len(start), len(end))):
        a = start[i] if i < len(start) else None
        b = end[i] if i < len(end) else None
        if a != b:
            pairs.append((a, b))
    out.append(f"Lines changed: {len(pairs)}\n", style="bold")
    for a, b in pairs[:shown]:
        out.append(f"- {a if a is not None else '(no line)'}\n", style="red")
        out.append(f"+ {b if b is not None else '(no line)'}\n", style="green")
    if len(pairs) > shown:
        out.append(f"…and {len(pairs) - shown} more\n", style="dim")
    return out


class MenuScreen(Screen):
    BINDINGS = [("q", "quit_app", "Quit")]

    def __init__(
        self, store: ProgressStore, regions: list[tuple[str, list[Level]]]
    ) -> None:
        super().__init__()
        self.store = store
        self.regions = regions
        self.levels = [lvl for _, lvls in regions for lvl in lvls]
        self._pending_tab = False
        # pane_id -> (region index, slug); slug per region for widget ids.
        self._panes: list[tuple[str, int]] = [
            (f"tab-{self._slug(name)}", i)
            for i, (name, _) in enumerate(regions)
        ]
        self._unlocked: dict[str, bool] = {}

    @staticmethod
    def _slug(name: str) -> str:
        return name.lower().replace(" ", "-")

    def _pane_id(self, region_index: int) -> str:
        return f"tab-{self._slug(self.regions[region_index][0])}"

    def _list_id(self, region_index: int) -> str:
        return f"list-{self._slug(self.regions[region_index][0])}"

    def _notice_id(self, region_index: int) -> str:
        return f"notice-{self._slug(self.regions[region_index][0])}"

    def region_final(self, region_index: int) -> Level:
        """Gatekeeper: highest-order level of a region."""
        return max(self.regions[region_index][1], key=lambda l: l.order)

    def is_unlocked(self, region_index: int) -> bool:
        if region_index == 0:
            return True
        final = self.region_final(region_index - 1)
        return self.store.progress.best_ranks.get(final.id) == MASTERY

    def unlock_notice(self, region_index: int) -> str:
        final = self.region_final(region_index - 1)
        name = self.regions[region_index][0]
        return (
            f"LOCKED — master '{final.title}' with Mastery "
            f"to unlock {name}."
        )

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="menu"):
            yield Static("[bold]NeoVim Quest[/bold]\n[dim]Learn real Neovim workflows by playing.[/dim]")
            yield Static(id="menu-progress")
            yield Static("[dim](j/k move, l opens, gt switches parts)[/dim]")
            with TabbedContent(initial=self._pane_id(0)):
                for i, (name, lvls) in enumerate(self.regions):
                    with TabPane(name, id=self._pane_id(i)):
                        with VerticalScroll(id=self._list_id(i)):
                            for lvl in lvls:
                                yield Button(self._label(lvl),
                                             id=f"level-{lvl.id}")
                            # Quit lives inside each tab's scroll list so it
                            # stays reachable (and visible) at any height.
                            yield Button("Quit", id=f"quit-{self._slug(name)}",
                                         variant="error", classes="quit-btn")
                        yield Static("", id=self._notice_id(i),
                                     classes="lock-notice")
        yield Footer()

    def _label(self, lvl: Level) -> str:
        rank = self.store.progress.best_ranks.get(lvl.id, "—")
        # Note: square brackets are parsed as markup by Button labels,
        # so the lesson goes in parentheses.
        return f"{lvl.title}  ({lvl.lesson})  best: {rank}"

    def _refresh(self) -> None:
        for lvl in self.levels:
            self.query_one(f"#level-{lvl.id}", Button).label = self._label(lvl)
        self.query_one("#menu-progress", Static).update(self._progress_text())
        for i, (name, lvls) in enumerate(self.regions):
            unlocked = self.is_unlocked(i)
            self._unlocked[self._pane_id(i)] = unlocked
            self.query_one(f"#{self._list_id(i)}",
                           VerticalScroll).display = unlocked
            notice = self.query_one(f"#{self._notice_id(i)}", Static)
            notice.display = not unlocked
            if not unlocked:
                notice.update(f"[yellow]{self.unlock_notice(i)}[/yellow]")

    def _progress_text(self) -> str:
        completed = set(self.store.progress.completed)
        parts = []
        for name, lvls in self.regions:
            done = sum(1 for lvl in lvls if lvl.id in completed)
            parts.append(f"{name}: {done}/{len(lvls)}")
        return "  ·  ".join(parts)

    def on_mount(self) -> None:
        self._refresh()
        buttons = self._buttons()
        if buttons:
            self.set_focus(buttons[0])

    def on_screen_resume(self) -> None:
        # Returning from a quest: ranks/progress/locks may have changed.
        self._refresh()

    # -- keyboard navigation (vim motions) ------------------------------

    def _active_pane_id(self) -> str:
        try:
            return self.query_one(TabbedContent).active
        except Exception:
            return self._pane_id(0)

    def _pane_region(self, pane_id: str) -> int:
        for pid, i in self._panes:
            if pid == pane_id:
                return i
        return 0

    def _buttons(self) -> list[Button]:
        """Focusable buttons: active tab's levels + its Quit button.

        On a locked tab only Quit is reachable (level buttons hidden).
        """
        pane_id = self._active_pane_id()
        region = self._pane_region(pane_id)
        try:
            pane = self.query_one(f"#{pane_id}", TabPane)
            buttons = list(pane.query(Button))
        except Exception:
            return []
        if not self._unlocked.get(pane_id, region == 0):
            buttons = [b for b in buttons if "quit-btn" in (b.classes or [])]
        return buttons

    def _move_focus(self, direction: int) -> None:
        buttons = self._buttons()
        if not buttons:
            return
        try:
            index = buttons.index(self.focused)
        except ValueError:
            index = 0 if direction > 0 else len(buttons) - 1
        else:
            index = (index + direction) % len(buttons)
        target = buttons[index]
        self.set_focus(target)
        # Focusing alone does not scroll: bring the button into view.
        # Unanimated so keyboard travel stays snappy (and testable).
        pane_id = self._active_pane_id()
        region = self._pane_region(pane_id)
        try:
            self.query_one(f"#{self._list_id(region)}",
                           VerticalScroll).scroll_to_widget(
                target, animate=False
            )
        except Exception:
            pass

    def _switch_tab(self, direction: int) -> None:
        try:
            tabbed = self.query_one(TabbedContent)
        except Exception:
            return
        panes = [pid for pid, _ in self._panes]
        try:
            index = panes.index(tabbed.active)
        except ValueError:
            index = 0
        tabbed.active = panes[(index + direction) % len(panes)]
        self._pending_tab = False
        # Focus follows the tab: first level, or Quit on a locked part.
        buttons = self._buttons()
        if buttons:
            self.set_focus(buttons[0])

    def _open_focused(self) -> None:
        focused = self.focused
        if not isinstance(focused, Button):
            return
        btn = focused.id or ""
        if btn == "quit" or btn.startswith("quit-"):
            self.app.exit()
        elif btn.startswith("level-"):
            level_id = btn[len("level-"):]
            level = next(l for l in self.levels if l.id == level_id)
            self.app.push_screen(QuestScreen(level, self.store))

    async def on_key(self, event) -> None:
        # Vim motions only: j/k move, l opens, gt/gT switch parts.
        # (Enter activates the focused button natively; q quits via binding.)
        key = event.key
        if key == "j":
            self._pending_tab = False
            self._move_focus(1)
            event.prevent_default()
        elif key == "k":
            self._pending_tab = False
            self._move_focus(-1)
            event.prevent_default()
        elif key == "l":
            self._pending_tab = False
            self._open_focused()
            event.prevent_default()
        elif key == "g":
            self._pending_tab = True
            event.prevent_default()
        elif key == "t" and self._pending_tab:
            self._switch_tab(1)
            event.prevent_default()
        elif key == "T" and self._pending_tab:
            self._switch_tab(-1)
            event.prevent_default()
        elif self._pending_tab:
            self._pending_tab = False

    @on(Button.Pressed)
    def _pressed(self, event: Button.Pressed) -> None:
        btn = event.button.id or ""
        if btn == "quit" or btn.startswith("quit-"):
            self.app.exit()
        elif btn.startswith("level-"):
            level_id = btn[len("level-"):]
            level = next(l for l in self.levels if l.id == level_id)
            self.app.push_screen(QuestScreen(level, self.store))

    def action_quit_app(self) -> None:
        self.app.exit()


class ResultsScreen(Screen):
    def __init__(self, level: Level, stats: AttemptStats, rank: str,
                 elapsed: float, history: list[CommandResult],
                 end_lines: list[str] | None = None) -> None:
        super().__init__()
        self.level = level
        self.stats = stats
        self.rank = rank
        self.elapsed = elapsed
        self.history = history
        self.end_lines = end_lines

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static("[bold]Quest Complete[/bold]")
            yield Static(id="results-body")
            yield Static(id="results-diff")
            yield Button("Back to Lessons", id="back", variant="primary")
        yield Footer()

    def on_mount(self) -> None:
        used = " ".join(r.command for r in self.history if not r.invalid)
        fams = ", ".join(sorted(self.stats.families_used)) or "—"
        if self.rank == "Mastery":
            verdict = "[green]Mastery achieved — flawless technique.[/green]"
        else:
            gaps = mastery_gaps(self.level, self.stats)
            verdict = (
                "[yellow]Next rank missed because: "
                + "; ".join(gaps)
                + "[/yellow]"
                if gaps
                else ""
            )
        self.query_one("#results-body", Static).update(
            f"[bold]{self.level.title}[/bold] — [yellow]{self.rank} Rank[/yellow]\n\n"
            f"Time: {_fmt_time(self.elapsed)}\n"
            f"Actions: {self.stats.actions} (reference: {self.level.reference_actions})\n"
            f"Mistakes: {self.stats.invalid}\n"
            f"Hints used: {self.stats.hints_used}\n"
            f"Motion families: {fams}\n"
            f"{verdict}\n\n"
            f"[dim]You used:[/dim] {used}"
        )
        self.query_one("#results-diff", Static).update(
            diff_text(self.level.start_text, self.end_lines)
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
    /* Full-width buttons: rank text ("—" → "Mastery") must never be
       cropped by a width measured from older, shorter labels. */
    TabPane VerticalScroll Button { width: 1fr; }
    TabPane VerticalScroll { height: 1fr; }
    #menu TabbedContent { height: 1fr; }
    .lock-notice { padding: 1 2; }
    #quest-title { padding: 0 1; }
    #quest-objective { padding: 0 1; color: #9ecbff; }
    #quest-allowed { padding: 0 1; }
    #quest-mastery { padding: 0 1; }
    #quest-targets { padding: 0 1; }
    #quest-buffer-scroll { height: 1fr; border: solid #444; }
    #quest-status { padding: 0 1; }
    """

    def __init__(self, store: ProgressStore | None = None) -> None:
        super().__init__()
        self.store = store or ProgressStore()
        self.regions = load_regions()
        self.levels = [lvl for _, lvls in self.regions for lvl in lvls]

    def on_mount(self) -> None:
        self.push_screen(MenuScreen(self.store, self.regions))
