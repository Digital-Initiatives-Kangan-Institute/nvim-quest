# NeoVim Quest Editing Region Plan (Region 2)

Status: implemented (14 levels, orders 21–34). Originally planned as 8;
expanded during build with `cc`, `r`, live insert, and `J` (see addendum).

## Goal

Modify text efficiently. ~8 levels across Delete, Change, Copy/Paste,
Repeating (per `neovim-quest-mvp-roadmap.md`). Same teaching style as
Navigation: introduce related commands together, contrast them in guided
chains, finish each lesson with an outcome-based challenge.

Unlike Navigation (content-only), Editing needs engine work first: the
simulation currently only moves a cursor.

## Part 1 — Engine: text mutation

### 1.1 Buffer operations (`simulation/buffer.py`)

Add line/character mutation primitives:

- `delete_char(row, col, count)` — remove N chars at cursor.
- `delete_range(start, end)` — charwise range `[start, end)`, may span lines
  (joining them, vim-style).
- `delete_lines(row, count)` — remove whole lines; never delete the last
  line (leave one empty line, vim-like).
- `insert_text(row, col, text)` — insert (possibly multi-line) text.
- `replace_range(start, end, text)` — delete then insert (for change).

Cursor rules after mutation: clamp into surviving text; after `dd`, move to
the first non-blank of the current line (vim-like).

### 1.2 Operators (`simulation/operators.py`, new)

Implement `d`, `c`, `y` composed with motions, plus standalone `x`:

- `x` — delete char under cursor, count supported. Empty range (end of an
  empty line) is a no-op.
- `dw` — delete to the start of the next word, **clamped to the line end**
  (simplification: real vim has end-of-line edge cases; document it, match
  the common case). Must also handle the `d` + `e`/`$`/`w` family generally:
  implement operator application over an arbitrary motion range, charwise.
- `dd` — linewise delete of `count` lines.
- `cw` — vim special case: behaves like `ce` (to word end), then insert.
- `ciw` — inner-word range (reuse word-boundary helpers from `motions.py`),
  then insert.
- `yy` — linewise yank of `count` lines (no buffer change).
- `p` — paste: linewise buffer pastes **below** the current line (`yy`, `dd`
  products); charwise buffer pastes **after** the cursor.

Out of scope (explicitly): `cc`, `P`, visual mode, `u` undo, named registers
(yank goes to one unnamed buffer; full registers are Region 4).

### 1.3 Change tracking: unnamed register + repeat

- `VirtualEditor` gains `unnamed: str | list[str]` (charwise vs linewise
  yank/delete product; deletes also populate it, vim-like) and
  `last_change` (operator + range + inserted text) for `.` repeat.
- `.` re-applies `last_change` at the current cursor. Yank is not repeatable.
- Parser extension (`state._parse`): operator-first forms —
  `[count]d{motion}`, `[count]c{motion}`, `[count]y{motion}`, `dd`, `yy`,
  `x`, `p`, `.`, e.g. `dw`, `d2w`, `2dd`, `ciw`, `yy`, `3p`(? keep `p`
  uncounted in MVP). Returns base keys `d` / `c` / `y` / `x` / `p` / `.`.
- `FAMILIES`: `x`, `d`, `c`, `y`, `p`, `.` → `edit`. No-op edits
  (empty range, paste of empty buffer, repeat with no prior change) are
  invalid, preserving the Silver mechanic.

### 1.4 Evaluation: text goals (`quest/`)

Level schema addition: `end_text: [...]` (expected buffer lines on success).
Evaluator completion becomes: all cursor targets visited (if any) **and**
buffer lines equal `end_text` (if present). Editing levels will mostly use
text goals alone; navigation warm-ups may combine both.

`MasteryRule.required_keys` already covers edit keys (`["x"]`, `["d"]`,
`["c"]`, `["y", "p"]`, `["."]`) — no scoring changes. `describe_mastery`
and `mastery_gaps` work unchanged ("never used .").

## Part 2 — UI: operator-pending and insert mode (`ui/quest_screen.py`)

- **Pending operator:** after `d`/`c`/`y` (with optional count), wait for the
  motion (`dw`, `dd`, `ciw`…); status shows the partial command; `Esc`
  cancels. Bare `d`/`c`/`y` followed by an invalid motion records one
  invalid action, not two.
- **Insert mode:** `c`-commands land in INSERT (`-- INSERT --` indicator,
  cursor style change). Typed text commits on `Enter` (and `Esc`, vim-like);
  counts as part of the same action for scoring. Empty commit = plain
  deletion (still valid).
- **Changed-line highlight:** dim lines identical to `start_text`, highlight
  modified lines, so progress is visible at a glance.
- **Results screen:** show a small before/after (changed line count + the
  commands used); rank verdicts already work via `mastery_gaps`.

`key_to_char` needs no alias additions (`d c y x p .` are single chars), but
the modifier-key guard must also cover pending-operator state.

## Part 3 — Levels (~8, orders 21–28, region `Editing`)

### Lesson: Delete (3)

- `editing_delete_01` "First Cut" (`x`): single line with typos
  (`exxample`), delete named characters. Mastery: `x`.
- `editing_delete_02` "Word Weeding" (`dw`): line of words, delete named
  words in order; contrast `dw` vs `x` (one weeds a word, one a char).
- `editing_delete_03` "Line Clearing" (`dd`): 5–6 line list, delete named
  lines; introduce counts (`2dd`). Mastery: `d` + within count.

### Lesson: Change (2–3)

- `editing_change_01` "New Wording" (`cw`): replace named words via
  `cw` + insert + Enter. Teaches delete-then-type as one action.
- `editing_change_02` "Inner Remedy" (`ciw`): cursor starts mid-word;
  `cw` would leave a fragment, `ciw` cleans the whole word — the contrast
  is the lesson. (Yes, `iw` previews Region 3; keep it mechanical here.)
- Optional `editing_change_03`: mixed `cw`/`ciw` chain without hints.

### Lesson: Copy and Paste (2)

- `editing_yank_01` "Duplicate Line" (`yy`/`p`): duplicate a config line
  below itself.
- `editing_yank_02` "Reorder" (`dd`/`p` or `yy`/`p` across distance):
  move a line past 2–3 others using navigation + paste. Combines Region 1
  motions with edits; allow full navigation set.

### Lesson: Repeating (1–2)

- `editing_repeat_01` "Do It Again" (`.`): 3+ lines needing the identical
  fix (e.g. `dw` on each, or `cw` same replacement); reference uses `.`
  so Gold requires it. Mastery: `.`.
- Optional `editing_repeat_02`: `.` with counts/mixed positions.

Suggested set: 3 + 2 + 2 + 1 = 8 levels (add the optionals if calibration
shows a lesson needs reinforcement).

## Part 4 — Tests

- Unit: buffer mutations (char/range/line, edge: last line, empty line),
  operator ranges (`dw` at line end, `dd` with count, `cw` ≡ `ce`,
  `ciw` mid-word), linewise vs charwise paste, `.` repeat incl. insert text,
  no-op edits marked invalid.
- Level tests: reference solution per level asserting `end_text` reached
  with Mastery at reference count (extend `test_levels.py` pattern).
- UI pilot: insert-mode flow (`cw` → type → Enter), pending-operator
  cancel, changed-line render.

## Build order

1. Buffer mutation ops + unit tests.
2. Operators + unnamed register + repeat + parser/families + unit tests.
3. Evaluator `end_text` + schema field.
4. UI pending-operator + insert mode + highlights + results diff.
5. Delete lesson levels → Change → Yank/put → Repeat, calibrating each
   (reference must earn Mastery).
6. Menu/ordering: loader already sorts by `order`; no changes expected.

## Addendum: scope expansions during build

- **`cc`**: accepted after review — linewise change reuses the `dd` path
  plus insert (~5 lines). Own level `editing_change_03`. `S` stays out
  (pure synonym); `C` already works via `c$`.
- **`r`**: replace-char operator with pending-char UI, `.` repeat, no
  register change. Level `editing_change_04`. Bare `R` (replace mode)
  stays out.
- **Live insert**: `i`/`a`/`o`/`O` entry with per-keystroke buffer editing
  (separate typing cursor, since normal cursors can't rest past EOL),
  `-- INSERT --` indicator, one action per session. Levels
  `editing_insert_01/02/03` (`a`, `o`+`O`, `i`).
- **`J`**: join lines (single space, indent stripped, counts join N).
  Lesson "Join", level `editing_join_01`.

Final region: Delete 3, Change 4, Copy/Paste 2, Repeat 1, Insert 3,
Join 1 = 14 levels (orders 21–34). Game total: 34 levels.

## Risks / open questions

- `dw` end-of-line semantics: simplified to clamp at line end; verify no
  level depends on the real-vim trailing-space nuance.
- Insert-mode commit key: `Enter` primary, `Esc` also commits — confirm no
  conflict with existing `Esc` (search-cancel) flows.
- Scope discipline: `cc`, `P`, `u`, visual mode stay out; named registers
  wait for Region 4 even though `yy`/`p` invite `"ay` curiosity (hint text
  can foreshadow it).
