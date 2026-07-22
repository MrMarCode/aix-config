#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/worktree.py"

if [ ! -f "$PYTHON_SCRIPT" ]; then
   echo "ERROR worktree.py not found at $SCRIPT_DIR" >&2
   exit 1
fi

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
VENV_PYTHON="$DATA_HOME/worktree/venv/bin/python"

if [ -x "$VENV_PYTHON" ]; then
   PYTHON="$VENV_PYTHON"
else
   PYTHON="python3"
fi

if [ -n "${WORKTREE_CONFIG:-}" ]; then
   set -- --config "$WORKTREE_CONFIG" "$@"
fi

exec "$PYTHON" "$PYTHON_SCRIPT" "$@"
