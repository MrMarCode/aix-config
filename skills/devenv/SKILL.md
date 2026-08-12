---
name: devenv
description:
  Per-repo isolated dev environments with devbox + direnv + 1Password
  secrets. Use when setting up project tooling that must never be
  committed, adding packages or env vars to a repo environment, or
  resolving op:// secrets. (2 supporting files)
---

# Devenv — Per-Repo Isolated Dev Environments

One `init` command gives a repo an auto-loading tool environment
(devbox packages + direnv activation + a `secrets` command for
1Password). None of the files are ever committed — they are covered by
the machine-global git ignore, live once at the repo's canonical path,
and are symlinked into every worktree by the worktree skill.

Requires `devbox`, `direnv` (hooked into the shell), `op`, `git`, and
`python3` with pyyaml.

## Setup for a repo

```bash
# Repo name from .worktree.yaml (run from the worktrees dir, or set
# WORKTREE_CONFIG)
devenv.sh init my-repo

# Or a direct path to a git repo not in the config
devenv.sh init /path/to/repo
```

`init` does all of this in one shot:

1. `devbox init` in the repo's canonical path (kept if already present)
2. Writes `.envrc` (devbox activation + `.env` loading + `.localbin` on
   PATH), `.env` template, and `.localbin/secrets`
3. `devbox install` to materialize `.devbox/` and `devbox.lock`
4. Adds all of these to the repo's `symlinks:` list in `.worktree.yaml`
   so `worktree create --symlink` wires new worktrees automatically
5. Ensures the global git ignore covers `devbox.json`, `devbox.lock`,
   `.devbox/`, `.direnv/`, `.envrc`, `.env`, `.localbin/`
6. Whitelists the worktrees dir and repo path in
   `~/.config/direnv/direnv.toml` so environments load without a manual
   `direnv allow` per worktree

Idempotent: re-running `init` never overwrites existing files, only
fills gaps.

## Daily use

- `cd` into the repo or any worktree — tools and plain env vars load
  automatically; leaving the directory unloads them.
- **Add a package**: `devbox add nodejs@20` (from any worktree — the
  config is shared per-repo, so all worktrees get it).
- **Add an env var**: edit `.env`. Plain values load on next prompt.
- **Secrets**: put `op://vault/item/field` references in `.env`. They
  stay literal until you run `secrets`, which starts a subshell with
  the references resolved by the 1Password CLI. Exit the subshell to
  drop them. Never resolve secrets automatically.

## How the pieces fit

- All files live once at `repos.<name>.path` from `.worktree.yaml`;
  worktrees only contain symlinks to them. Editing in any worktree
  edits the shared file.
- The worktree skill stays environment-agnostic — it only symlinks the
  paths listed in its config.
- Generated state (`.devbox/`, `devbox.lock`) is shared per-repo too.
  Known edge: a tool that replaces a symlinked file via
  rename-over-write turns it into a real per-worktree file — if an
  environment diverges, delete the stray file and re-run
  `worktree create --symlink` or re-link manually.
