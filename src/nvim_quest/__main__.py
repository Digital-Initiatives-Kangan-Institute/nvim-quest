"""Entry point: `nvim-quest` or `python -m nvim_quest`."""

from __future__ import annotations

from .ui.app import NvimQuestApp


def main() -> None:
    # Keyboard-only by design (a vim game): no terminal mouse reporting,
    # so text selection keeps working and every action is a keypress.
    NvimQuestApp().run(mouse=False)


if __name__ == "__main__":
    main()
