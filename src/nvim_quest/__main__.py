"""Entry point: `nvim-quest` or `python -m nvim_quest`."""

from __future__ import annotations

from .ui.app import NvimQuestApp


def main() -> None:
    NvimQuestApp().run()


if __name__ == "__main__":
    main()
