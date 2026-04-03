---
name: worktree
description:
  Manage git worktrees for parallel development. Use when creating,
  removing, or listing worktrees for a repository. Supports config-based
  repo resolution and optional symlinking of shared files.
---

# Worktree — Git Worktree Manager

Shell tool (`worktree.sh` in this skill directory) for creating,
removing, and listing git worktrees with optional symlink support.

Requires `git` and `yq`.

## Workflow

1. Run `worktree.sh list` (no args) to see all configured repos
2. If a matching repo exists, use its name as the first argument
3. If no config exists yet, create a `.worktree.yaml` for the user

```bash
# Show all configured repos
worktree.sh list

# Show worktrees for a specific repo
worktree.sh list my-repo

# Create worktree with default symlinks from config
worktree.sh create my-repo feature/auth --symlink

# Create worktree with custom symlink list
worktree.sh create my-repo bugfix/login --symlink 'node_modules,.env'

# Create worktree by direct path (no config needed)
worktree.sh create ./my-repo experiment/perf

# Remove a worktree
worktree.sh remove my-repo feature/auth
```

The worktree directory is created in the current working directory,
named after the branch (with `/` replaced by `-`).

`--symlink` uses the symlink list from `.worktree.yaml`. Pass a
comma-separated override to `--symlink 'a,b'` instead.

## Config file (`.worktree.yaml`)

If no config exists, suggest creating one so repo names and default
symlinks work. Override the path with `WORKTREE_CONFIG` env var.

```yaml
default:
  symlinks:
    - node_modules
repos:
  my-repo:
    path: /home/user/code/my-repo
    symlinks:
      - node_modules
      - .env
```
