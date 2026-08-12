#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -n "${WORKTREE_CONFIG:-}" ]; then
   set -- "$@" --config "$WORKTREE_CONFIG"
fi

exec python3 "$SCRIPT_DIR/devenv.py" "$@"
