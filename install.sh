#!/usr/bin/env bash
#
# Install NeoVim Quest.
#
# Usage:
#   ./install.sh          install for the current Python
#   ./install.sh --dev    editable install with dev/test dependencies
#
# Afterwards, launch the game with:  nvim-quest
#
set -euo pipefail

DEV=0
if [[ "${1:-}" == "--dev" ]]; then
    DEV=1
elif [[ -n "${1:-}" ]]; then
    echo "Usage: $0 [--dev]" >&2
    exit 2
fi

PYTHON="${PYTHON:-python3}"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "error: $PYTHON not found. Install Python 3.10 or newer first." >&2
    exit 1
fi

"$PYTHON" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' || {
    echo "error: Python 3.10+ required (found $("$PYTHON" --version 2>&1))." >&2
    exit 1
}

if [ "$DEV" -eq 1 ]; then
    "$PYTHON" -m pip install -e ".[dev]"
else
    "$PYTHON" -m pip install .
fi

if ! command -v nvim-quest >/dev/null 2>&1; then
    echo "warning: installed, but 'nvim-quest' is not on PATH." >&2
    echo "Try: $PYTHON -m nvim_quest" >&2
    exit 0
fi

echo "Installed. Launch the game with:  nvim-quest"
