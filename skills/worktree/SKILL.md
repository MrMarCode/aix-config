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

Requires `git` and `yq`. Do not use runbox for this command.

## Workflow

1. Run `worktree.sh list` (no args) to see all configured repos
2. If a matching repo exists, use its name as the first argument
3. If no config exists yet, create a `.worktree.yaml` for the user

```bash
# Show all configured repos
worktree.sh list

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
repos:
  my-repo:
    path: /home/user/code/my-repo
    symlinks:
      - node_modules
      - .env
```
