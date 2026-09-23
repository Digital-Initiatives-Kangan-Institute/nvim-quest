"""Quest screen: buffer view, target checklist, vim-style key handling."""

from __future__ import annotations

import time
import unicodedata

from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.keys import KEY_TO_UNICODE_NAME, REPLACED_KEYS
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from ..progress.store import ProgressStore
from ..quest.evaluator import Evaluator
from ..quest.models import Level
from ..quest.scoring import describe_mastery, rank_attempt

PENDING_FIND = {"f", "t"}
IMMEDIATE = {"h", "j", "k", "l", "w", "b", "e", "0", "^", "$", "G", "n", "N"}


def format_allowed_motions(level: Level, keys_used: set[str]) -> str:
    """Render the allowed-motions line with usage coloring.

    Used motions show green, newly introduced (but unused) ones yellow,
    the rest plain — so the player sees what they have already tried.
    """
    new = {c for c in level.introduced if c in level.allowed_set}
    parts = []
    for cmd in level.allowed_commands:
        if cmd in keys_used:
            parts.append(f"[green]{cmd}[/green]")
        elif cmd in new:
            parts.append(f"[yellow]{cmd}[/yellow]")
        else:
            parts.append(cmd)
    return (
        "[bold]Allowed motions:[/bold] "
        + " ".join(parts)
        + "  [dim](green = used, yellow = new)[/dim]"
    )

try:
    # Authoritative bare-modifier key names (Kitty keyboard protocol
    # reports Shift/Ctrl/... presses as their own key events).
    from textual._keyboard_protocol import MODIFIER_FUNCTIONAL_KEYS as _MODIFIERS

    MODIFIER_KEYS = frozenset(_MODIFIERS)
except ImportError:  # pragma: no cover - fallback if Textual internals move
    MODIFIER_KEYS = frozenset(
        {
            "left_shift",
            "left_control",
            "left_alt",
            "left_super",
            "left_hyper",
            "left_meta",
            "right_shift",
            "right_control",
            "right_alt",
            "right_super",
            "right_hyper",
            "right_meta",
            "iso_level3_shift",
            "iso_level5_shift",
        }
    )


def key_to_char(key: str) -> str:
    """Translate a Textual key name to the typed character.

    Single-character keys pass through. Named keys (``circumflex_accent``,
    ``dollar_sign``, ``comma``, ``slash``, ...) are resolved via the
    Unicode name table so Shift+6 (^), Shift+4 ($), f+comma etc. work in a
    real terminal. Non-printable / non-ASCII keys yield "".
    """
    if len(key) == 1:
        return key if key.isascii() and key.isprintable() else ""
    uname = KEY_TO_UNICODE_NAME.get(key)
    if uname is None:
        # Friendly names ("slash") map back to Unicode names ("SOLIDUS").
        uname = REPLACED_KEYS.get(key, key).upper().replace("_", " ")
    try:
        char = unicodedata.lookup(uname)
    except KeyError:
        return ""
    if len(char) == 1 and char.isascii() and char.isprintable():
        return char
    return ""


class QuestScreen(Screen):
    """Play one level. Keys act as vim normal-mode commands."""

    BINDINGS = [
        ("ctrl+q", "quit_level", "Quit level"),
    ]

    def __init__(self, level: Level, store: ProgressStore) -> None:
        super().__init__()
        self.level = level
        self.store = store
        self.ev = Evaluator(level)
        self.start_time = time.monotonic()
        self.count_buf = ""
        self.pending_g = False
        self.pending_find = ""
        self.message = "Move with the lesson's motions. '/' search, '?' hint."
        self.hint_index = 0
        self.finished = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield Static(id="quest-title")
            yield Static(id="quest-objective")
            yield Static(id="quest-allowed")
            yield Static(id="quest-mastery")
            yield Static(id="quest-targets")
            with VerticalScroll(id="quest-buffer-scroll"):
                for r in range(len(self.level.start_text)):
                    yield Static(id=f"quest-line-{r}")
            yield Static(id="quest-status")
            yield Input(placeholder="type search term, Enter to search, Esc to cancel",
                        id="search-input")
        yield Footer()

    def on_mount(self) -> None:
        search_input = self.query_one("#search-input", Input)
        search_input.display = False
        search_input.disabled = True
        self.refresh_all()

    # -- rendering ------------------------------------------------------

    def refresh_all(self) -> None:
        lvl = self.level
        self.query_one("#quest-title", Static).update(
            f"[bold]{lvl.title}[/bold]  [dim]({lvl.lesson} · {lvl.id})[/dim]"
        )
        self.query_one("#quest-objective", Static).update(
            f"[bold]Objective:[/bold] {lvl.objective}"
        )
        allowed = format_allowed_motions(lvl, self.ev.stats.keys_used)
        self.query_one("#quest-allowed", Static).update(allowed)
        self.query_one("#quest-mastery", Static).update(
            f"[dim]{describe_mastery(lvl)}[/dim]"
        )
        lines = []
        for i, t in enumerate(lvl.targets):
            if i < self.ev.current_target_index:
                lines.append(f"  [green]✓ {t.label}[/green]")
            elif i == self.ev.current_target_index:
                lines.append(f"  [bold yellow]→ {t.label}[/bold yellow]")
            else:
                lines.append(f"  [dim]· {t.label}[/dim]")
        self.query_one("#quest-targets", Static).update("\n".join(lines))
        nlines = len(self.ev.editor.buf.lines)
        for r in range(nlines):
            self.query_one(f"#quest-line-{r}", Static).update(self._render_line(r))
        # Keep the cursor line visible in large documents.
        cursor_widget = self.query_one(
            f"#quest-line-{self.ev.editor.pos[0]}", Static
        )
        self.query_one("#quest-buffer-scroll", VerticalScroll).scroll_to_widget(
            cursor_widget, animate=False
        )
        pos = self.ev.editor.pos
        self.query_one("#quest-status", Static).update(
            f"Cursor: line {pos[0] + 1}, col {pos[1] + 1}   "
            f"Actions: {self.ev.stats.actions}   "
            f"Mistakes: {self.ev.stats.invalid}   "
            f"Hints: {self.ev.stats.hints_used}\n"
            f"[dim]{self.message}[/dim]"
        )

    def _render_line(self, r: int) -> Text:
        out = Text()
        line = self.ev.editor.buf.lines[r]
        cursor = self.ev.editor.pos
        cur_target = (
            self.level.targets[self.ev.current_target_index]
            if self.ev.current_target_index < len(self.level.targets)
            else None
        )
        matches = set(self.ev.editor.search.matches)
        shown = line if line else " "
        for c, ch in enumerate(shown):
            style = ""
            if (r, c) == cursor:
                style = "reverse bold"
            elif cur_target is not None and (r, c) == cur_target.pos:
                style = "bold yellow underline"
            elif (r, c) in matches:
                style = "on dark_green"
            out.append(ch if line else "·", style=style or None)
        return out

    # -- input state machine --------------------------------------------

    async def on_key(self, event) -> None:
        if self.finished:
            return
        if event.key in MODIFIER_KEYS:
            # Bare modifier press (e.g. Shift held for 'f('). Never part of
            # a command — ignore it without disturbing pending f/t/g/count.
            event.prevent_default()
            return
        search_input = self.query_one("#search-input", Input)
        if search_input.display and not search_input.disabled:
            if event.key == "escape":
                search_input.display = False
                search_input.disabled = True
                search_input.value = ""
                self.set_focus(None)
                self.message = "Search cancelled."
                self.refresh_all()
                event.prevent_default()
            return  # Input widget handles its own keys

        key = event.key
        char = key_to_char(key)
        # '0' alone is a motion; a leading digit starts a count.
        if char.isdigit() and not self.pending_find and not self.pending_g:
            if char == "0" and not self.count_buf:
                self._run("0")
            else:
                self.count_buf += char
                self.message = f"Count: {self.count_buf}"
                self.refresh_all()
            event.prevent_default()
            return

        if self.pending_find:
            if char:
                self._run(f"{self.count_buf}{self.pending_find}{char}")
            else:
                self.message = "Find cancelled."
                self.refresh_all()
            self.pending_find = ""
            self.count_buf = ""
            event.prevent_default()
            return

        if self.pending_g:
            self.pending_g = False
            if char == "g":
                self._run("gg")
            else:
                self.message = "'g' alone does nothing — press 'gg'."
                self.count_buf = ""
                self.refresh_all()
            event.prevent_default()
            return

        if char == "g":
            self.pending_g = True
            self.message = "Pressed 'g' — press 'g' again for 'gg'."
            self.refresh_all()
        elif char in PENDING_FIND and char in self.level.allowed_set:
            self.pending_find = char
            self.message = f"Pressed '{char}' — type the target character."
            self.refresh_all()
        elif char == "/":
            if char not in self.level.allowed_set:
                # Search would trivialize non-search lessons: refuse it
                # up front instead of opening a prompt that can only fail.
                self.message = (
                    "Search isn't part of this lesson — "
                    "use the lesson's motions instead."
                )
                self.count_buf = ""
                self.refresh_all()
            else:
                search_input.display = True
                search_input.disabled = False
                search_input.value = ""
                search_input.focus()
                self.message = "Type a search term and press Enter."
                self.refresh_all()
        elif char == "?":
            self._hint()
        elif char and (char in IMMEDIATE or char in ("f", "t")):
            self._run(f"{self.count_buf}{char}")
            self.count_buf = ""
        else:
            self.count_buf = ""
            return  # let bindings (ctrl+q etc.) work
        event.prevent_default()

    @on(Input.Submitted, "#search-input")
    def _search_submitted(self, event: Input.Submitted) -> None:
        term = event.value
        search_input = self.query_one("#search-input", Input)
        search_input.display = False
        search_input.disabled = True
        search_input.value = ""
        self.set_focus(None)
        if term:
            self._run(f"/{term}")
        else:
            self.message = "Empty search — nothing happened."
            self.refresh_all()

    def _run(self, command: str) -> None:
        hit, done = self.ev.submit(command)
        last = self.ev.editor.history[-1]
        if last.invalid:
            self.message = f"'{command}' had no effect (invalid here)."
        elif hit:
            if done:
                self.message = "All targets reached!"
            else:
                nxt = self.level.targets[self.ev.current_target_index].label
                self.message = f"Target reached — next: {nxt}"
        else:
            self.message = f"Moved to line {last.pos[0] + 1}, col {last.pos[1] + 1}."
        self.refresh_all()
        if done:
            self._finish()

    def _hint(self) -> None:
        hints = self.level.hints
        if not hints:
            self.message = "No hints for this level."
        else:
            self.ev.use_hint()
            self.hint_index = min(self.hint_index, len(hints) - 1)
            self.message = f"Hint: {hints[self.hint_index]}"
            self.hint_index = min(self.hint_index + 1, len(hints) - 1)
        self.refresh_all()

    def _finish(self) -> None:
        self.finished = True
        elapsed = time.monotonic() - self.start_time
        rank = rank_attempt(self.level, self.ev.stats)
        if rank != "Locked":
            self.store.record(self.level.id, rank, self.ev.stats.actions)
        from .app import ResultsScreen

        self.app.push_screen(
            ResultsScreen(self.level, self.ev.stats, rank, elapsed,
                          self.ev.editor.history)
        )

    def action_quit_level(self) -> None:
        self.app.pop_screen()
