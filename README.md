# NeoVim Quest

A console-based learning game that teaches real NeoVim workflows through
interactive challenges. Instead of memorising commands, you solve practical
navigation scenarios and learn to think like a NeoVim user.

## Install

Requires Python 3.10+.

```bash
./install.sh          # install for the current Python
./install.sh --dev    # editable install with test dependencies
```

Manual alternatives:

```bash
pip install .         # from the repo root
pip install -e ".[dev]"  # editable + dev dependencies
pipx install .        # isolated install
```

## Play

```bash
nvim-quest            # or: python -m nvim_quest
```

- **Menu:** `j`/`k` move, `l` (or Enter) opens a level, `q` quits.
- **Levels:** keys act as Vim normal-mode commands — `h j k l w b e
  0 ^ $ gg G f<char> t<char> /term n N`, with counts (`7j`, `3w`).
  `/` opens search, `?` shows a hint, `Ctrl+Q` quits the level.
- **Ranks:** Bronze (finish) → Silver (no mistakes) → Gold (within the
  reference action count) → Mastery (required motions, no hints).
  The quest screen shows which motions you've used and what Mastery needs;
  the results screen explains what blocked the next rank.

## Content

20 Navigation levels: Character Motion (3), Word Motion (4), Efficient
Motion/counts (1), Line and Document Motion (5), Character Finding (2),
Search (3), and two final challenges including the 45-line Grand Archive.
See `docs/` for the architecture, MVP roadmap, and region specification.

## Project layout

```text
src/nvim_quest/
  simulation/   virtual editor: buffer, motions, search
  quest/        level models, loader, evaluator, scoring
  progress/     local save data
  ui/           Textual app: menu, quest, results screens
src/nvim_quest/content/navigation/   the 20 level definitions (YAML, shipped in the package)
tests/          unit, level-solution, and headless UI tests
```

## Development

```bash
pytest            # full test suite (71 tests)
```

Progress is saved to `~/.local/share/nvim-quest/save.json`
(`$XDG_DATA_HOME` respected when set).
