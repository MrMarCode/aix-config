---
name: workspace
description:
  Manage development workspaces — git worktrees plus per-repo isolated dev
  environments (devbox + direnv + 1Password secrets). Use when creating,
  removing, or browsing workspaces for a repo, or when setting up project
  tooling that must never be committed. (2 supporting files)
---

# Workspace — Worktrees and Per-Repo Dev Environments

`workspace.py` in this skill directory manages git worktrees
("workspaces") and per-repo dev environments. `workspace.sh` is a thin
wrapper that uses the local venv when it exists.

Requires `git` and `python3`. Dependencies install into a local virtual
environment when you run `install`; never install them globally. The
`init` command additionally requires `devbox`, `direnv`, and `op`.

## Workflow

1. Run `workspace.sh install` to create the local venv and install the
   `workspace` shell function.
2. Run `workspace` with no arguments to open the projects grid: one box
   per configured repo showing its name, workspace count, and last
   activity. Nothing is fetched at this level, so it opens instantly.
3. Select a project to open its window: workspaces newest to oldest,
   with the canonical repo (mainline) as the top row. Opening the window
   fetches origin in the background and fast-forwards the mainline only
   when the working tree is clean and strictly behind; a dirty or
   diverged repo shows a warning instead.
4. Use `workspace init <repo>` once per repo to give it an isolated dev
   environment. Its files are then symlinked into every new workspace.

```bash
# Install shell function and dependencies (zsh, bash, or auto-detect)
workspace.sh install
workspace.sh install --shell zsh,bash

# Projects grid (default entry point)
workspace

# Flat interactive list of every workspace by recent activity
workspace list --all

# Show all configured repos
workspace list --configured

# Show worktrees for a specific repo
workspace list my-repo

# List workspaces merged into origin's default branch
workspace list merged

# Create a workspace — configured symlinks are created by default
workspace create my-repo feature/auth

# Create without symlinks
workspace create my-repo feature/auth --no-symlink

# Override the symlink list
workspace create my-repo bugfix/login --symlink 'node_modules,.env'

# Branch a new workspace from a specific ref (stacked branches)
workspace create my-repo feature/auth-part-2 --base-ref feature/auth

# Create at a custom subdirectory (nested dirs are created)
workspace create my-repo feature/auth --path category/custom

# Create by direct repo path (no config needed)
workspace create ./my-repo experiment/perf

# Remove a workspace (looks up the path by branch, so custom paths work)
workspace remove my-repo feature/auth

# Remove every workspace whose branch is merged into origin's default branch
workspace remove merged

# Open in the configured editor / diff tool
workspace open my-repo feature/auth
workspace open my-repo feature/auth --editor code
workspace diff my-repo feature/auth

# Metadata
workspace meta my-repo feature/auth
workspace meta my-repo feature/auth --title "Auth fix" --link "Plan=https://example.org/plan"
workspace meta my-repo feature/auth --ticket https://dev.azure.com/.../12345

# Set up an isolated dev environment for a repo
workspace init my-repo
workspace init /path/to/repo
```

## TUI keys

Projects grid: arrow keys move, `Enter` opens the project, `r` refreshes,
`q` quits.

Project window:

```
Enter  cd into the selected workspace (or the mainline repo)
o      open in the editor
d      open in the diff tool
c      cd and start claude
n      new workspace (branch name, base ref, optional workspace name)
r      refresh
q/Esc  back to the grid
```

`n` prefills the base ref with the repo's `default_branch` (or
`origin/HEAD`); override it to stack a branch on another. The optional
workspace name overrides the branch-derived directory name. New
workspaces are created in the directory the TUI was launched from, with
symlinks on.

## How `cd` works

`install` writes a `workspace` shell function. It creates a temp file,
passes its path as `WORKSPACE_CMD_FILE`, and evals the file after the
tool exits. The TUI writes `cd '<dir>'` — or `cd '<dir>' && exec claude`
— to that file, so the directory change lands in the calling shell.

## Config file (`.workspace.yaml`)

If no config exists, suggest creating one so repo names and default
symlinks work. Override the path with the `WORKSPACE_CONFIG` env var. A
legacy `.worktree.yaml` in the current directory is still read, with a
warning telling you to `mv` it.

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
    default_branch: develop
    skip_mtime_dirs:
      - dist
      - build
```

Editor resolution priority: `--editor` flag → repo `editor` → default
`editor` → `pycharm`. Diff resolution priority: `--diff` flag → repo
`diff` → default `diff` → the editor.

`skip_mtime_dirs` adds directories to skip when computing the most
recent file change. The default skip list already includes `.git`,
`node_modules`, `__pycache__`, `.venv`, `venv`, `.tox`, `dist`, `build`,
`target`, `.next`, `coverage`, and `.mypy_cache`.

`list merged` / `remove merged` detect the default branch via
`git symbolic-ref refs/remotes/origin/HEAD` (or
`repos.<name>.default_branch`), then match merge commits on that branch
whose message contains the workspace's branch name.

## Workspace metadata

Metadata lives in `~/.local/share/workspace/workspace_metadata.yaml`
(or under `XDG_DATA_HOME`), keyed by workspace path, so workspaces
created outside this tool are supported:

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
```

## Dev environments (`workspace init`)

One `init` gives a repo an auto-loading tool environment (devbox
packages + direnv activation + a `secrets` command for 1Password). None
of the files are ever committed — they are covered by the machine-global
git ignore, live once at the repo's canonical path, and are symlinked
into every workspace.

`init` does all of this in one shot:

1. `devbox init` in the repo's canonical path (kept if already present)
2. Writes `.envrc` (devbox activation + `.env` loading + `.localbin` on
   PATH), an `.env` template, and `.localbin/secrets`
3. `devbox install` to materialize `.devbox/` and `devbox.lock`
4. Adds all of these to the repo's `symlinks:` list in the config, so
   `workspace create` wires new workspaces automatically
5. Ensures the global git ignore covers `devbox.json`, `devbox.lock`,
   `.devbox/`, `.direnv/`, `.envrc`, `.env`, `.localbin/`, `.venv/`
6. Whitelists the workspaces dir and repo path in
   `~/.config/direnv/direnv.toml` so environments load without a manual
   `direnv allow` per workspace

Idempotent: re-running `init` never overwrites existing files, only
fills gaps.

### Daily use

- `cd` into the repo or any workspace — tools and plain env vars load
  automatically; leaving the directory unloads them.
- **Add a package**: `devbox add nodejs@20` (from any workspace — the
  config is shared per-repo).
- **Python projects**: add python as `python@3.10` (the name devbox's
  plugin recognizes — a raw flake ref like `github:...#python310` does
  NOT trigger it). The plugin creates a `.venv`; install libraries with
  `devbox run -- "$VENV_DIR/bin/pip" install boto3`. The generated
  `.envrc` puts `$VENV_DIR/bin` on PATH automatically.
- **Pinned packages**: devbox accepts flake refs for old versions, e.g.
  `devbox add "github:NixOS/nixpkgs/<rev>#ansible_2_12"`.
- **Add an env var**: edit `.env`. Plain values load on next prompt.
- **Secrets**: put `op://vault/item/field` references in `.env`. They
  stay literal until you run `secrets`, which starts a subshell with the
  references resolved by the 1Password CLI. Exit the subshell to drop
  them. Never resolve secrets automatically.

Known edge: a tool that replaces a symlinked file via
rename-over-write turns it into a real per-workspace file — if an
environment diverges, delete the stray file and re-create the symlink.
