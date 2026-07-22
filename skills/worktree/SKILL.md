---
name: worktree
description:
  Manage git worktrees for parallel development. Use when creating,
  removing, or listing worktrees for a repository. Supports config-based
  repo resolution and optional symlinking of shared files.
  (1 supporting files)
---

# Worktree — Git Worktree Manager

Python tool (`worktree.py` in this skill directory) for creating,
removing, and listing git worktrees with optional symlink support.
`worktree.sh` is a thin wrapper that delegates to the Python script
for backwards compatibility.

Requires `git` and `python3`. Dependencies are installed into a local
virtual environment when you run `install`; do not install them globally.

## Workflow

1. Run `worktree.sh install` to create a local venv and install the
   `worktree` shell function
2. Run `worktree list` (no args) to see an interactive list of recent
   worktrees, or `worktree list --configured` to see all configured repos
3. In the list, press `Enter`, `c`, or click a row to `cd` into that
   worktree. Press `o` to open in the editor, `d` to open in the diff
   tool, and `r` to refresh. The list is sorted by the most recent file
   change, skipping artifact directories like `node_modules`.
4. The detail panel at the bottom shows metadata for the highlighted
   worktree, including clickable links to tickets or plans.
5. If a matching repo exists, use its name as the first argument.
6. If no config exists in the current directory, the last used config
   file is remembered and reused automatically.
7. If no config exists yet, create a `.worktree.yaml` for the user.

```bash
# Install shell function and dependencies (zsh, bash, or auto-detect)
worktree.sh install
worktree.sh install --shell zsh
worktree.sh install --shell bash,zsh

# Interactive list of all worktrees sorted by recent file changes
# Use arrow keys/mouse to move, Enter to cd, o to open, d to diff
worktree.sh list

# Show all configured repos (old no-args behavior)
worktree.sh list --configured

# Show worktrees for a specific repo
worktree.sh list my-repo

# List worktrees merged into origin's default branch (across all configured repos)
worktree.sh list merged

# Create worktree with default symlinks from config
worktree.sh create my-repo feature/auth --symlink

# Create worktree with custom symlink list
worktree.sh create my-repo bugfix/login --symlink 'node_modules,.env'

# Create worktree at a custom subdirectory (nested dirs are created)
worktree.sh create my-repo feature/auth --path category/custom --symlink

# Create worktree by direct path (no config needed)
worktree.sh create ./my-repo experiment/perf

# Remove a worktree (looks up the path by branch, so custom paths work)
worktree.sh remove my-repo feature/auth

# Remove every worktree whose branch has been merged into origin's default branch
worktree.sh remove merged

# Open a worktree in the configured editor (default: pycharm)
worktree.sh open my-repo feature/auth

# Open with a specific editor override
worktree.sh open my-repo feature/auth --editor code

# Open a worktree in the configured diff tool (falls back to editor)
worktree.sh diff my-repo feature/auth

# Open with a specific diff tool override
worktree.sh diff my-repo feature/auth --diff pycharm

# TUI keybindings:
#   Enter or c  cd into selected worktree (requires shell function)
#   o           open in editor
#   d           open in diff tool
#   r           refresh list
#   q           quit

# View metadata for a worktree
worktree.sh meta my-repo feature/auth

# Add title and a link to a worktree
worktree.sh meta my-repo feature/auth --title "Auth fix" --link "Plan=https://example.org/plan"

# Add a ticket URL
worktree.sh meta my-repo feature/auth --ticket https://dev.azure.com/.../12345
```

By default the worktree directory is created in the current working
directory, named after the branch (with `/` replaced by `-`). Use
`--path <subdir>` to override.

`--symlink` uses the symlink list from `.worktree.yaml`. Pass a
comma-separated override to `--symlink 'a,b'` instead.

`list merged` / `remove merged` detect the default branch via
`git symbolic-ref refs/remotes/origin/HEAD` (or
`repos.<name>.default_branch` in config), then match merge commits on
that branch whose message contains the worktree's branch name.

## Config file (`.worktree.yaml`)

If no config exists, suggest creating one so repo names and default
symlinks work. Override the path with `WORKTREE_CONFIG` env var.

```yaml
default:
  symlinks:
    - node_modules
  editor: windsurf
  diff: pycharm
repos:
  my-repo:
    path: /home/user/code/my-repo
    symlinks:
      - node_modules
      - .env
    editor: code
    diff: pycharm
    skip_mtime_dirs:
      - dist
      - build
```

Editor resolution priority: `--editor` CLI flag → repo-level
`editor` → default-level `editor` → `pycharm`.

Diff resolution priority: `--diff` CLI flag → repo-level `diff` →
default-level `diff` → repo-level `editor` → default-level `editor` →
`pycharm`.

`skip_mtime_dirs` at the repo or default level adds directories to skip
when computing the most recent file change. The default skip list already
includes `.git`, `node_modules`, `__pycache__`, `.venv`, `venv`, `.tox`,
`dist`, `build`, `target`, `.next`, `coverage`, and `.mypy_cache`.

## Worktree metadata

Metadata is stored separately from config in
`~/.local/share/worktree/worktree_metadata.yaml` (or under `XDG_DATA_HOME`).
It is keyed by worktree path so worktrees created outside of this tool are
supported. The metadata file is a simple YAML document:

```yaml
worktrees:
  /home/user/code/my-repo/feature-auth:
    title: "Auth fix"
    notes: "Waiting for API review"
    tickets:
      - https://dev.azure.com/.../12345
    links:
      - label: "Plan"
        url: https://example.org/plan
      - https://example.org/spec
```

Use `worktree meta` to view or edit metadata from the command line. The
interactive list displays the title, notes, tickets, and links in the
detail panel, with links rendered as terminal hyperlinks when the terminal
supports them.

`install` writes a `worktree` shell function instead of a simple alias so
that `Enter` in the interactive list can change the current shell
directory. `worktree.sh` remains a backwards-compatible wrapper that uses
the local venv when it exists.
