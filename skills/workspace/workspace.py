#!/usr/bin/env python3
"""Workspace manager: git worktrees, dev environments, and an interactive TUI."""

import os
import sys
import subprocess
import argparse
from datetime import datetime, timezone
from pathlib import Path

try:
   import yaml
except ImportError:
   yaml = None


DEFAULT_CONFIG_FILE = '.workspace.yaml'
LEGACY_CONFIG_FILE = '.worktree.yaml'
DEFAULT_EDITOR = 'pycharm'
DEFAULT_METADATA_FILE = 'workspace_metadata.yaml'
LEGACY_METADATA_FILE = 'worktree_metadata.yaml'
DEFAULT_SKIP_MTIME_DIRS = {
   '.git', 'node_modules', '__pycache__', '.venv', 'venv', '.tox', 'dist',
   'build', 'target', '.next', 'coverage', '.mypy_cache',
}


def get_state_dir():
   """@return Path - directory for persistent state."""
   data_home = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
   state_dir = data_home / 'workspace'
   state_dir.mkdir(parents=True, exist_ok=True)
   return state_dir


def get_last_config_path():
   """@return Path - file storing the last successfully used config path."""
   return get_state_dir() / 'last_config'


def get_metadata_path():
   """@return Path - file storing workspace metadata."""
   state_dir = get_state_dir()
   current = state_dir / DEFAULT_METADATA_FILE
   if current.is_file():
      return current

   legacy = state_dir / LEGACY_METADATA_FILE
   if legacy.is_file():
      return legacy

   return current


def get_shell_command_file():
   """@return Path|None - file the shell wrapper evals after the TUI exits."""
   path = os.environ.get('WORKSPACE_CMD_FILE', '')
   return Path(path) if path else None


def write_shell_command(command):
   """
   Hand a command back to the shell wrapper so it runs in the user's shell.

   @param str command - shell command, e.g. "cd '/path'"
   @return bool - True if the wrapper will run it
   """
   cmd_file = get_shell_command_file()
   if not cmd_file:
      print(command)
      return False

   cmd_file.write_text(f'{command}\n')
   return True


def shell_quote(value):
   """@return str - single-quoted value safe for a shell command."""
   escaped = str(value).replace("'", "'\\''")
   return f"'{escaped}'"


def cd_command(path, run_claude=False):
   """
   @param str path - directory to change into
   @param bool run_claude - append `&& exec claude`
   @return str - shell command for the wrapper to eval
   """
   command = f'cd {shell_quote(path)}'
   if run_claude:
      return f'{command} && exec claude'
   return command


def load_metadata():
   """
   @return dict - metadata keyed by worktree path
   """
   if yaml is None:
      return {}

   path = get_metadata_path()
   if not path.is_file():
      return {}

   parsed = yaml.safe_load(path.read_text()) or {}
   if isinstance(parsed, dict) and 'worktrees' in parsed:
      return parsed['worktrees'] or {}
   return parsed


def save_metadata(metadata):
   """
   @param dict metadata - metadata keyed by worktree path
   """
   if yaml is None:
      return

   path = get_metadata_path()
   path.parent.mkdir(parents=True, exist_ok=True)
   path.write_text(
      yaml.safe_dump(
         {'worktrees': metadata},
         default_flow_style=False,
         sort_keys=False,
      )
   )


def resolve_config_path(config_path):
   """
   Resolve the config file path, falling back to the last known config.

   @param str|None config_path - explicit CLI config path
   @return str - path to use
   """
   if config_path:
      return config_path

   env_path = (
      os.environ.get('WORKSPACE_CONFIG', '')
      or os.environ.get('WORKTREE_CONFIG', '')
   )
   if env_path:
      return env_path

   cwd_config = Path.cwd() / DEFAULT_CONFIG_FILE
   if cwd_config.is_file():
      return str(cwd_config)

   legacy_config = Path.cwd() / LEGACY_CONFIG_FILE
   if legacy_config.is_file():
      _print_warning(
         f'Using legacy {LEGACY_CONFIG_FILE} — rename it with: '
         f'mv {LEGACY_CONFIG_FILE} {DEFAULT_CONFIG_FILE}'
      )
      return str(legacy_config)

   last_config = get_last_config_path()
   if last_config.is_file():
      saved = last_config.read_text().strip()
      if saved and Path(saved).is_file():
         return saved

   return str(cwd_config)


def safe_branch_dir(branch):
   """Replace `/` with `-` to create a filesystem-safe directory name."""
   return branch.replace('/', '-')


def load_config(config_path):
   """
   @param str config_path - path to the YAML config file
   @return dict - parsed config, or empty dict if file missing
   """
   if yaml is None:
      _exit_error(
         'YAML is required but not installed. '
         'Run: workspace.py install'
      )

   path = Path(config_path)
   if not path.is_file():
      return {}

   parsed = yaml.safe_load(path.read_text()) or {}
   if parsed:
      get_last_config_path().write_text(str(path.resolve()))
   return parsed


def resolve_repo(name, config):
   """
   @param str name - repo key from config, or direct path to a git repo
   @param dict config - parsed config
   @return str - absolute path to the git repo
   """
   repos = config.get('repos', {})
   if name in repos:
      repo_path = repos[name].get('path', '')
      if repo_path:
         return repo_path

   candidate = Path(name)
   if (candidate / '.git').is_dir() or (candidate / '.git').is_file():
      return str(candidate)

   if repos:
      _exit_error(
         f"'{name}' not found in config and is not a path to a git repo"
      )
   _exit_error(f"'{name}' is not a path to a git repo and no config file found")


def resolve_symlinks(name, config, inline_override):
   """
   @param str name - repo key
   @param dict config - parsed config
   @param str inline_override - comma-separated override list, or empty
   @return list[str] - symlink items
   """
   if inline_override:
      return [s.strip() for s in inline_override.split(',') if s.strip()]

   if not config:
      return []

   repos = config.get('repos', {})
   repo_config = repos.get(name, {})
   repo_symlinks = repo_config.get('symlinks', [])
   if repo_symlinks:
      return repo_symlinks

   return config.get('default', {}).get('symlinks', [])


def is_git_repo(path):
   """@return bool - True if path contains a .git dir or file."""
   p = Path(path)
   return (p / '.git').is_dir() or (p / '.git').is_file()


def git(repo_path, *args, check=True, capture=True):
   """
   Run a git command in the given repo.

   @param str repo_path - path to the git repo
   @param str *args - git subcommand and arguments
   @param bool check - raise on non-zero exit (default True)
   @param bool capture - capture stdout (default True)
   @return subprocess.CompletedProcess
   """
   cmd = ['git', '-C', repo_path] + list(args)
   return subprocess.run(
      cmd,
      check=check,
      capture_output=capture,
      text=True,
   )


def branch_exists(repo_path, branch):
   """@return bool - True if branch exists locally or on origin."""
   for ref in (f'refs/heads/{branch}', f'refs/remotes/origin/{branch}'):
      result = git(repo_path, 'show-ref', '--verify', '--quiet', ref, check=False)
      if result.returncode == 0:
         return True
   return False


def worktree_path_for_branch(repo_path, branch):
   """
   @param str repo_path - path to the git repo
   @param str branch - branch name
   @return str|None - absolute path to the worktree, or None
   """
   result = git(repo_path, 'worktree', 'list', '--porcelain')
   entries = parse_worktree_porcelain(result.stdout)
   for entry in entries:
      if entry.get('branch') == branch:
         return entry.get('path')
   return None


def parse_worktree_porcelain(output):
   """
   Parse `git worktree list --porcelain` output into a list of dicts.

   @param str output - raw porcelain output
   @return list[dict] - each dict has 'path' and optionally 'branch'
   """
   entries = []
   current = {}
   for line in output.splitlines():
      if not line:
         if current:
            entries.append(current)
            current = {}
         continue
      if line.startswith('worktree '):
         current['path'] = line[len('worktree '):]
      elif line.startswith('branch refs/heads/'):
         current['branch'] = line[len('branch refs/heads/'):]
   if current:
      entries.append(current)
   return entries


def create_symlinks(repo_path, worktree_dir, symlink_items):
   """
   Create symlinks from repo_path into worktree_dir.

   @param str repo_path - source repo path
   @param str worktree_dir - target worktree path
   @param list[str] symlink_items - relative paths to symlink
   """
   for item in symlink_items:
      source = Path(repo_path) / item
      target = Path(worktree_dir) / item

      if not source.exists():
         _print_warning(f"{item} not found at {source} — skipping")
         continue

      target.parent.mkdir(parents=True, exist_ok=True)
      target.symlink_to(source.resolve())


def default_branch(repo_path, config, name):
   """
   Determine the default branch for a repo.

   @param str repo_path - path to the git repo
   @param dict config - parsed config
   @param str name - repo key
   @return str - default branch name
   """
   repos = config.get('repos', {})
   repo_config = repos.get(name, {})
   override = repo_config.get('default_branch', '')
   if override:
      return override

   result = git(
      repo_path, 'symbolic-ref', '--quiet',
      'refs/remotes/origin/HEAD', check=False,
   )
   if result.returncode == 0 and result.stdout.strip():
      ref = result.stdout.strip()
      return ref.removeprefix('refs/remotes/origin/')

   for candidate in ('master', 'main'):
      check = git(
         repo_path, 'show-ref', '--verify', '--quiet',
         f'refs/remotes/origin/{candidate}', check=False,
      )
      if check.returncode == 0:
         return candidate

   return None


def resolve_editor(name, config, override):
   """
   Determine which editor command to use.

   Priority: CLI override → repo config → default config → DEFAULT_EDITOR

   @param str name - repo key
   @param dict config - parsed config
   @param str override - CLI-provided editor override, or empty
   @return str - editor command
   """
   if override:
      return override

   repos = config.get('repos', {})
   repo_editor = repos.get(name, {}).get('editor', '')
   if repo_editor:
      return repo_editor

   default_editor = config.get('default', {}).get('editor', '')
   if default_editor:
      return default_editor

   return DEFAULT_EDITOR


def resolve_diff(name, config, override):
   """
   Determine which diff tool command to use.

   Priority: CLI override → repo diff → default diff → editor

   @param str name - repo key
   @param dict config - parsed config
   @param str override - CLI-provided diff override, or empty
   @return str - diff tool command
   """
   if override:
      return override

   repos = config.get('repos', {})
   repo_diff = repos.get(name, {}).get('diff', '')
   if repo_diff:
      return repo_diff

   default_diff = config.get('default', {}).get('diff', '')
   if default_diff:
      return default_diff

   return resolve_editor(name, config, '')


def resolve_skip_mtime_dirs(name, config):
   """
   Build the set of directory names to skip when checking mtime.

   Defaults are always skipped; config can add more.

   @param str name - repo key
   @param dict config - parsed config
   @return set[str] - directory names to skip
   """
   if not config:
      return set(DEFAULT_SKIP_MTIME_DIRS)

   repos = config.get('repos', {})
   repo_extra = repos.get(name, {}).get('skip_mtime_dirs', [])
   default_extra = config.get('default', {}).get('skip_mtime_dirs', [])

   return set(DEFAULT_SKIP_MTIME_DIRS) | set(default_extra) | set(repo_extra)


def is_merged_to_default(repo_path, branch, default_br):
   """
   @param str repo_path - path to the git repo
   @param str branch - branch name to check
   @param str default_br - default branch name
   @return bool - True if branch appears in a merge commit on default
   """
   result = git(
      repo_path, 'log', f'origin/{default_br}', '--merges',
      '-F', '--grep', branch, '-n', '1', '--format=%H',
      check=False,
   )
   return bool(result.stdout.strip())


def list_merged_worktrees(config):
   """
   @param dict config - parsed config
   @return list[dict] - each dict: name, branch, worktree_path, repo_path
   """
   repos = config.get('repos', {})
   merged = []

   for name, repo_config in repos.items():
      repo_path = repo_config.get('path', '')
      if not repo_path or not is_git_repo(repo_path):
         continue

      default_br = default_branch(repo_path, config, name)
      if not default_br:
         _print_warning(
            f"Cannot determine default branch for {repo_path} — skipping"
         )
         continue

      main_result = git(repo_path, 'rev-parse', '--show-toplevel', check=False)
      main_worktree = main_result.stdout.strip() if main_result.returncode == 0 else ''

      result = git(repo_path, 'worktree', 'list', '--porcelain')
      entries = parse_worktree_porcelain(result.stdout)

      for entry in entries:
         wt_path = entry.get('path', '')
         wt_branch = entry.get('branch', '')
         if not wt_path or not wt_branch:
            continue
         if wt_path == main_worktree:
            continue
         if is_merged_to_default(repo_path, wt_branch, default_br):
            merged.append({
               'name': name,
               'branch': wt_branch,
               'worktree_path': wt_path,
               'repo_path': repo_path,
            })

   return merged


# -- Alias / dependency installation ---------------------------------

def get_script_dir():
   """@return Path - directory containing this script."""
   return Path(__file__).resolve().parent


def get_venv_dir():
   """@return Path - local venv used for worktree dependencies."""
   data_home = Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))
   return data_home / 'workspace' / 'venv'


def get_requirements_txt():
   """@return Path - requirements.txt next to this script."""
   return get_script_dir() / 'requirements.txt'


def get_shell_rc(shell):
   """
   @param str shell - 'zsh' or 'bash'
   @return Path - path to the shell's rc file
   """
   home = Path.home()
   if shell == 'zsh':
      return home / '.zshrc'
   if shell == 'bash':
      return home / '.bashrc'
   _exit_error(f"Unsupported shell: {shell}")


def get_shell_function(venv_dir, script_path):
   """
   Build a shell function that wraps workspace.py and evals its command file.

   The TUI writes a command (`cd '<dir>'`, optionally `&& exec claude`) to
   WORKSPACE_CMD_FILE; the function evals it so it affects the caller's shell.

   @param Path venv_dir - local virtual environment
   @param Path script_path - path to workspace.py
   @return str - shell function to append
   """
   python = venv_dir / 'bin' / 'python'
   return f"""workspace() {{
   local cmd_file rc
   cmd_file="$(mktemp "${{TMPDIR:-/tmp}}/workspace-cmd.XXXXXX")"
   WORKSPACE_CMD_FILE="$cmd_file" {python} {script_path} "$@"
   rc=$?
   if [ -s "$cmd_file" ]; then
      eval "$(cat "$cmd_file")"
      rc=$?
   fi
   rm -f "$cmd_file"
   return $rc
}}"""


def update_shell_rc(shell, venv_dir, script_path):
   """
   Add or replace the workspace shell function in the shell's rc file.

   @param str shell - 'zsh' or 'bash'
   @param Path venv_dir - local virtual environment
   @param Path script_path - path to workspace.py
   """
   rc = get_shell_rc(shell)
   function = get_shell_function(venv_dir, script_path)

   existing = rc.read_text() if rc.is_file() else ''
   marker = '# generated by workspace.py install'
   if marker in existing:
      return

   with open(rc, 'a') as f:
      f.write(f'\n{marker}\n{function}\n')
   print(f"Added workspace function to {rc}")


def install_venv(venv_dir):
   """
   Create a virtual environment and install this skill's requirements.

   @param Path venv_dir - target directory
   """
   venv_dir.parent.mkdir(parents=True, exist_ok=True)
   subprocess.run(
      [sys.executable, '-m', 'venv', str(venv_dir)],
      check=True,
   )

   pip = venv_dir / 'bin' / 'pip'
   requirements = get_requirements_txt()
   if requirements.is_file():
      subprocess.run(
         [str(pip), 'install', '--upgrade', 'pip'],
         check=True,
      )
      subprocess.run(
         [str(pip), 'install', '-r', str(requirements)],
         check=True,
      )


def cmd_install(shells):
   """
   Install the `workspace` shell function and local dependencies.

   @param list[str] shells - list of 'zsh' and/or 'bash'; empty means auto-detect
   """
   script_path = get_script_dir() / 'workspace.py'
   venv_dir = get_venv_dir()

   if not venv_dir.is_dir():
      print('Creating virtual environment...')
      install_venv(venv_dir)
      print('Dependencies installed.')

   if not shells:
      shell_name = os.path.basename(os.environ.get('SHELL', ''))
      if shell_name in ('zsh', 'bash'):
         shells = [shell_name]
      else:
         shells = ['zsh', 'bash']

   for shell in shells:
      update_shell_rc(shell, venv_dir, script_path)

   print(f"Run 'source <rc-file>' or start a new shell to use the function.")


# -- Recent activity helpers -----------------------------------------

def format_relative_time(timestamp):
   """
   @param float timestamp - seconds since epoch
   @return str - human-readable relative time
   """
   if timestamp is None:
      return 'never'

   now = datetime.now(timezone.utc)
   dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
   delta = now - dt

   seconds = int(delta.total_seconds())
   if seconds < 60:
      return 'just now'
   if seconds < 3600:
      return f'{seconds // 60}m ago'
   if seconds < 86400:
      return f'{seconds // 3600}h ago'
   if seconds < 604800:
      return f'{seconds // 86400}d ago'
   if seconds < 2419200:
      return f'{seconds // 604800}w ago'
   return f'{seconds // 2592000}mo ago'


def get_worktree_mtime(worktree_path, skip_dirs=None):
   """
   Find the most recent file modification time inside a worktree.

   @param str worktree_path - path to a worktree
   @param set[str]|None skip_dirs - directory names to skip (defaults to DEFAULT_SKIP_MTIME_DIRS)
   @return float|None - newest mtime, or None if no files are found
   """
   worktree = Path(worktree_path)
   if not worktree.is_dir():
      return None

   if skip_dirs is None:
      skip_dirs = DEFAULT_SKIP_MTIME_DIRS

   newest = None
   for root, dirs, files in os.walk(worktree):
      dirs[:] = [d for d in dirs if d not in skip_dirs]
      for f in files:
         if f in skip_dirs:
            continue
         try:
            mtime = (Path(root) / f).stat().st_mtime
            if newest is None or mtime > newest:
               newest = mtime
         except (OSError, PermissionError):
            continue
   return newest


def get_all_worktrees(config):
   """
   Collect all worktrees from configured repos with their most recent activity.

   @param dict config - parsed config
   @return list[dict] - worktree entries with name, branch, path, mtime, metadata
   """
   repos = config.get('repos', {})
   metadata = load_metadata()
   entries = []

   for name, repo_config in repos.items():
      repo_path = repo_config.get('path', '')
      if not repo_path or not is_git_repo(repo_path):
         continue

      result = git(repo_path, 'worktree', 'list', '--porcelain', check=False)
      if result.returncode != 0:
         continue

      main_result = git(repo_path, 'rev-parse', '--show-toplevel', check=False)
      main_worktree = main_result.stdout.strip() if main_result.returncode == 0 else ''

      skip_dirs = resolve_skip_mtime_dirs(name, config)

      for entry in parse_worktree_porcelain(result.stdout):
         wt_path = entry.get('path', '')
         wt_branch = entry.get('branch', '')
         if not wt_path or not wt_branch:
            continue
         if wt_path == main_worktree:
            continue

         mtime = get_worktree_mtime(wt_path, skip_dirs)
         entries.append({
            'name': name,
            'branch': wt_branch,
            'worktree_path': wt_path,
            'repo_path': repo_path,
            'mtime': mtime,
            'ago': format_relative_time(mtime),
            'metadata': metadata.get(wt_path, {}),
         })

   return sorted(entries, key=lambda e: (e['mtime'] or 0), reverse=True)


def build_tui_worktrees(config):
   """
   Build a flat, last-modified-first list of worktree entries for the TUI.

   @param dict config - parsed config
   @return list[dict] - worktree entries with display_path, editor, diff
   """
   worktrees = get_all_worktrees(config)

   for entry in worktrees:
      repo_path = entry['repo_path']
      wt_path = entry['worktree_path']
      try:
         display_path = os.path.relpath(wt_path, repo_path)
      except ValueError:
         display_path = wt_path

      entry['display_path'] = display_path
      entry['editor'] = resolve_editor(entry['name'], config, '')
      entry['diff'] = resolve_diff(entry['name'], config, '')

   return worktrees


def count_worktrees(repo_path):
   """
   @param str repo_path - path to the git repo
   @return int - number of linked worktrees, excluding the canonical repo
   """
   result = git(repo_path, 'worktree', 'list', '--porcelain', check=False)
   if result.returncode != 0:
      return 0

   main_result = git(repo_path, 'rev-parse', '--show-toplevel', check=False)
   main_worktree = main_result.stdout.strip() if main_result.returncode == 0 else ''

   entries = parse_worktree_porcelain(result.stdout)
   return len([e for e in entries if e.get('path') and e['path'] != main_worktree])


def build_projects(config):
   """
   Build one entry per configured repo for the projects grid.

   No network calls are made so the grid renders instantly.

   @param dict config - parsed config
   @return list[dict] - project entries with counts and last-activity age
   """
   repos = config.get('repos', {})
   projects = []

   for name, repo_config in repos.items():
      repo_path = repo_config.get('path', '')
      if not repo_path or not is_git_repo(repo_path):
         continue

      skip_dirs = resolve_skip_mtime_dirs(name, config)
      mtime = get_worktree_mtime(repo_path, skip_dirs)
      projects.append({
         'name': name,
         'repo_path': repo_path,
         'count': count_worktrees(repo_path),
         'mtime': mtime,
         'ago': format_relative_time(mtime),
         'editor': resolve_editor(name, config, ''),
         'diff': resolve_diff(name, config, ''),
      })

   return sorted(projects, key=lambda p: (p['mtime'] or 0), reverse=True)


def build_project_worktrees(config, name):
   """
   Build the rows for a single project window: mainline first, then worktrees.

   @param dict config - parsed config
   @param str name - repo key
   @return list[dict] - rows newest-first, with a mainline row at index 0
   """
   repo_path = resolve_repo(name, config)
   skip_dirs = resolve_skip_mtime_dirs(name, config)
   editor = resolve_editor(name, config, '')
   diff = resolve_diff(name, config, '')

   rows = [
      entry for entry in build_tui_worktrees(config)
      if entry['name'] == name
   ]

   branch_result = git(repo_path, 'rev-parse', '--abbrev-ref', 'HEAD', check=False)
   mtime = get_worktree_mtime(repo_path, skip_dirs)
   mainline = {
      'name': name,
      'branch': branch_result.stdout.strip() or '(detached)',
      'worktree_path': repo_path,
      'repo_path': repo_path,
      'display_path': repo_path,
      'mtime': mtime,
      'ago': format_relative_time(mtime),
      'metadata': load_metadata().get(repo_path, {}),
      'editor': editor,
      'diff': diff,
      'mainline': True,
      'status': 'fetching...',
   }

   return [mainline] + rows


def sync_mainline(repo_path):
   """
   Fetch origin and fast-forward the canonical repo when it is safe to do so.

   Only fast-forwards a clean working tree that is strictly behind upstream.

   @param str repo_path - path to the canonical repo
   @return str - short status message for display
   """
   fetch = git(repo_path, 'fetch', '--prune', check=False)
   if fetch.returncode != 0:
      return 'fetch failed'

   upstream = git(
      repo_path, 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}',
      check=False,
   )
   if upstream.returncode != 0 or not upstream.stdout.strip():
      return 'no upstream'

   counts = git(
      repo_path, 'rev-list', '--left-right', '--count', 'HEAD...@{upstream}',
      check=False,
   )
   if counts.returncode != 0:
      return 'unknown'

   parts = counts.stdout.split()
   ahead, behind = (int(parts[0]), int(parts[1])) if len(parts) == 2 else (0, 0)

   if ahead and behind:
      return f'WARNING diverged ({ahead} ahead, {behind} behind)'
   if ahead:
      return f'{ahead} ahead'
   if not behind:
      return 'up to date'

   dirty = git(repo_path, 'status', '--porcelain', check=False)
   if dirty.stdout.strip():
      return f'WARNING dirty, {behind} behind — not fast-forwarded'

   merge = git(repo_path, 'merge', '--ff-only', '@{upstream}', check=False)
   if merge.returncode != 0:
      return f'WARNING could not fast-forward ({behind} behind)'
   return f'fast-forwarded {behind}'


def create_workspace(config, name, branch, base_ref, dir_name, parent_dir,
                     symlinks=True):
   """
   Create a worktree for a repo, used by both the CLI and the TUI.

   @param dict config - parsed config
   @param str name - repo key or path
   @param str branch - branch to check out or create
   @param str base_ref - ref to branch from when the branch is new, or empty
   @param str dir_name - directory name, or empty to derive from the branch
   @param str parent_dir - directory the worktree is created in
   @param bool symlinks - create the configured symlinks (default True)
   @return str - path to the new worktree
   """
   repo_path = resolve_repo(name, config)
   if not is_git_repo(repo_path):
      _exit_error(f"Git repo not found at: {repo_path}")

   worktree_dir = str(Path(parent_dir) / (dir_name or safe_branch_dir(branch)))
   if Path(worktree_dir).exists():
      _exit_error(f"Path already exists: {worktree_dir}")

   Path(worktree_dir).parent.mkdir(parents=True, exist_ok=True)

   if branch_exists(repo_path, branch):
      git(repo_path, 'worktree', 'add', worktree_dir, branch, capture=False)
   elif base_ref:
      git(
         repo_path, 'worktree', 'add', '-b', branch, worktree_dir, base_ref,
         capture=False,
      )
   else:
      git(repo_path, 'worktree', 'add', '-b', branch, worktree_dir, capture=False)

   if symlinks:
      items = resolve_symlinks(name, config, '')
      if items:
         create_symlinks(repo_path, worktree_dir, items)

   return worktree_dir


def cmd_grid(config_path):
   """
   Launch the projects grid: one box per configured repo.

   @param str config_path - path to config file
   """
   config = load_config(config_path)
   if not config:
      _exit_error(f"No config file found at {config_path}")

   projects = build_projects(config)
   if not projects:
      print("No configured repos found")
      return

   try:
      from workspace_tui import WorkspaceApp
   except ImportError:
      _exit_error('textual is required for the grid. Run: workspace install')

   app = WorkspaceApp(config, config_path)
   app.run()


def cmd_list_interactive(config_path):
   """
   Launch an interactive UI listing worktrees by recent activity.

   @param str config_path - path to config file
   """
   config = load_config(config_path)
   if not config:
      _exit_error(f"No config file found at {config_path}")

   worktrees = get_all_worktrees(config)
   if not worktrees:
      print("No worktrees found")
      return

   try:
      from workspace_tui import WorktreeListApp
   except ImportError:
      print("Last modified\tBranch\tProject\tPath")
      for entry in worktrees:
         try:
            display_path = os.path.relpath(entry['worktree_path'], entry['repo_path'])
         except ValueError:
            display_path = entry['worktree_path']
         print(
            f"{entry['ago']}\t{entry['branch']}\t"
            f"{entry['name']}\t{display_path}"
         )
      return

   while True:
      worktrees = build_tui_worktrees(config)
      if not worktrees:
         print("No worktrees found")
         return

      app = WorktreeListApp(worktrees)
      result = app.run()
      if result == 1:
         continue
      if result:
         write_shell_command(result)
      break


# -- Commands --------------------------------------------------------

def cmd_create(name, branch, symlink_flag, symlink_items, custom_path,
               config_path, base_ref=''):
   """
   Create a worktree, symlinking shared files by default.

   @param str name - repo name or path
   @param str branch - branch to check out
   @param bool symlink_flag - whether to create symlinks (default True)
   @param str symlink_items - comma-separated override, or empty
   @param str custom_path - custom subdirectory, or empty
   @param str config_path - path to config file
   @param str base_ref - ref to branch from for new branches, or empty
   """
   config = load_config(config_path)
   if not config and symlink_flag and not symlink_items:
      _print_warning(
         f"No config file found at {config_path} — symlinking disabled"
      )

   repo_path = resolve_repo(name, config)
   if not is_git_repo(repo_path):
      _exit_error(f"Git repo not found at: {repo_path}")

   dir_name = custom_path if custom_path else safe_branch_dir(branch)
   worktree_dir = str(Path.cwd() / dir_name)

   if Path(worktree_dir).exists():
      _exit_error(f"Path already exists: {worktree_dir}")

   Path(worktree_dir).parent.mkdir(parents=True, exist_ok=True)

   if branch_exists(repo_path, branch):
      git(repo_path, 'worktree', 'add', worktree_dir, branch, capture=False)
   elif base_ref:
      git(
         repo_path, 'worktree', 'add', '-b', branch, worktree_dir, base_ref,
         capture=False,
      )
   else:
      git(repo_path, 'worktree', 'add', '-b', branch, worktree_dir, capture=False)

   if symlink_flag:
      items = resolve_symlinks(name, config, symlink_items)
      if items:
         create_symlinks(repo_path, worktree_dir, items)

   print(worktree_dir)


def cmd_remove(name, branch, config_path):
   """
   Remove a worktree by repo name and branch.

   @param str name - repo name or path
   @param str branch - branch whose worktree to remove
   @param str config_path - path to config file
   """
   config = load_config(config_path)
   repo_path = resolve_repo(name, config)

   wt_dir = worktree_path_for_branch(repo_path, branch)
   if not wt_dir:
      dir_name = safe_branch_dir(branch)
      wt_dir = str(Path.cwd() / dir_name)
      if not Path(wt_dir).is_dir():
         _exit_error(
            f"No worktree found for branch '{branch}' in {repo_path}"
         )

   git(repo_path, 'worktree', 'remove', wt_dir, '--force', capture=False)
   print(f"Removed {wt_dir}")


def cmd_remove_merged(config_path):
   """Remove all worktrees whose branches are merged into default."""
   config = load_config(config_path)
   if not config:
      _exit_error(f"No config file found at {config_path}")

   merged = list_merged_worktrees(config)
   if not merged:
      print("No merged worktrees found")
      return

   for entry in merged:
      print(
         f"Removing {entry['worktree_path']} "
         f"(repo: {entry['name']}, branch: {entry['branch']})"
      )
      git(
         entry['repo_path'], 'worktree', 'remove',
         entry['worktree_path'], '--force', capture=False,
      )


def cmd_list_repo(name, config_path):
   """
   List worktrees for a specific repo.

   @param str name - repo name or path
   @param str config_path - path to config file
   """
   config = load_config(config_path)
   repo_path = resolve_repo(name, config)
   git(repo_path, 'worktree', 'list', capture=False)


def cmd_list(name, config_path, configured=False):
   """
   Dispatch list behavior: interactive, all configured, or repo-specific.

   @param str name - repo name/path, 'merged', or None
   @param str config_path - path to config file
   @param bool configured - True to list all configured repos
   """
   if configured:
      cmd_list_all(config_path)
   elif name is None:
      cmd_list_interactive(config_path)
   elif name == 'merged':
      cmd_list_merged(config_path)
   else:
      cmd_list_repo(name, config_path)


def cmd_list_all(config_path):
   """List all configured repos from config."""
   config = load_config(config_path)
   if not config:
      _exit_error(f"No config file found at {config_path}")

   repos = config.get('repos', {})
   for name, repo_config in repos.items():
      print(f"{name}\t{repo_config.get('path', '')}")


def cmd_open(name, branch, config_path, editor_override):
   """
   Open a worktree directory in the configured editor.

   @param str name - repo name or path
   @param str branch - branch whose worktree to open
   @param str config_path - path to config file
   @param str editor_override - CLI-provided editor, or empty
   """
   config = load_config(config_path)
   repo_path = resolve_repo(name, config)

   wt_dir = resolve_worktree_dir(repo_path, branch)
   if not wt_dir:
      return

   editor = resolve_editor(name, config, editor_override)
   subprocess.Popen(
      [editor, wt_dir],
      start_new_session=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
   )
   print(f"Opened {wt_dir} in {editor}")


def cmd_diff(name, branch, config_path, diff_override):
   """
   Open a worktree directory in the configured diff tool.

   @param str name - repo name or path
   @param str branch - branch whose worktree to diff
   @param str config_path - path to config file
   @param str diff_override - CLI-provided diff tool, or empty
   """
   config = load_config(config_path)
   repo_path = resolve_repo(name, config)

   wt_dir = resolve_worktree_dir(repo_path, branch)
   if not wt_dir:
      return

   diff = resolve_diff(name, config, diff_override)
   subprocess.Popen(
      [diff, wt_dir],
      start_new_session=True,
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL,
   )
   print(f"Opened {wt_dir} in {diff}")


def resolve_worktree_dir(repo_path, branch):
   """
   Find the worktree directory for a branch, falling back to a local dir.

   @param str repo_path - path to the git repo
   @param str branch - branch name
   @return str|None - absolute worktree path, or None if not found
   """
   wt_dir = worktree_path_for_branch(repo_path, branch)
   if wt_dir:
      return wt_dir

   dir_name = safe_branch_dir(branch)
   wt_dir = str(Path.cwd() / dir_name)
   if Path(wt_dir).is_dir():
      return wt_dir

   _exit_error(f"No worktree found for branch '{branch}' in {repo_path}")


def cmd_meta(name, branch, config_path, title, notes, tickets, links, clear):
   """
   View or update metadata for a worktree.

   @param str name - repo name or path
   @param str branch - branch whose worktree to edit
   @param str config_path - path to config file
   @param str title - optional title
   @param str notes - optional notes
   @param list[str] tickets - optional ticket URLs
   @param list[str] links - optional link strings (label=url or url)
   @param bool clear - if True, remove all metadata for this worktree
   """
   config = load_config(config_path)
   repo_path = resolve_repo(name, config)
   wt_dir = resolve_worktree_dir(repo_path, branch)
   if not wt_dir:
      return

   metadata = load_metadata()

   if clear:
      metadata.pop(wt_dir, None)
      save_metadata(metadata)
      print(f"Removed metadata for {wt_dir}")
      return

   wt_meta = metadata.get(wt_dir, {})

   if title:
      wt_meta['title'] = title
   if notes:
      wt_meta['notes'] = notes
   if tickets:
      existing = wt_meta.get('tickets', [])
      for ticket in tickets:
         if ticket not in existing:
            existing.append(ticket)
      wt_meta['tickets'] = existing
   if links:
      existing = wt_meta.get('links', [])
      for link in links:
         if '=' in link:
            label, url = link.split('=', 1)
            item = {'label': label, 'url': url}
         else:
            item = link
         if item not in existing:
            existing.append(item)
      wt_meta['links'] = existing

   if not (title or notes or tickets or links):
      print(yaml.safe_dump({wt_dir: wt_meta}, default_flow_style=False, sort_keys=False))
      return

   metadata[wt_dir] = wt_meta
   save_metadata(metadata)
   print(yaml.safe_dump({wt_dir: wt_meta}, default_flow_style=False, sort_keys=False))


def cmd_list_merged(config_path):
   """List all worktrees whose branches are merged into default."""
   config = load_config(config_path)
   if not config:
      _exit_error(f"No config file found at {config_path}")

   merged = list_merged_worktrees(config)
   if not merged:
      print("No merged worktrees found")
      return

   rows = [
      f"{e['name']}  {e['branch']}  {e['worktree_path']}"
      for e in merged
   ]
   print('\n'.join(rows))


# -- Dev environment setup (devbox + direnv + op secrets) ------------

DEVENV_SYMLINK_ITEMS = [
   'devbox.json', 'devbox.lock', '.envrc', '.env', '.devbox', '.localbin', '.venv',
]

GLOBAL_IGNORE_HEADER = '# workspace skill — per-repo dev environment files (never committed)'
GLOBAL_IGNORE_PATTERNS = [
   'devbox.json',
   'devbox.lock',
   '.devbox/',
   '.direnv/',
   '.envrc',
   '.env',
   '.localbin/',
   '.venv/',
]

ENVRC_TEMPLATE = '''# Managed by the workspace skill. Never tracked in git (global ignore).
eval "$(devbox generate direnv --print-envrc)"

# Plain values load into the environment; op:// references stay literal
# until you run `secrets`.
dotenv_if_exists .env

PATH_add .localbin

# devbox's python plugin sets VENV_DIR; put its venv on PATH for
# direnv-loaded shells too (devbox only activates it in devbox shell).
if [ -n "${VENV_DIR:-}" ]; then
   PATH_add "$VENV_DIR/bin"
fi
'''

ENV_TEMPLATE = '''# Project env vars. Plain values load automatically via direnv.
# op:// secret references are NOT resolved automatically — run `secrets`
# to start a subshell with them injected by the 1Password CLI.
# EXAMPLE_TOKEN=op://vault/item/field
'''

SECRETS_TEMPLATE = '''#!/usr/bin/env bash
# Start a subshell with op:// references in .env resolved by 1Password CLI.
# Exit the subshell to drop the resolved secrets.
set -euo pipefail

root="$(git rev-parse --show-toplevel)"
echo "INFO Starting subshell with secrets from $root/.env — exit to drop them"
exec op run --env-file="$root/.env" -- "${SHELL:-zsh}"
'''


def run_command(cmd, cwd=None):
   """
   Run a command, failing loudly on error.

   @param list[str] cmd - command and args
   @param Path cwd - working directory (optional)
   """
   result = subprocess.run(cmd, cwd=cwd)

   if result.returncode != 0:
      _exit_error(f'Command failed: {" ".join(cmd)}')


def ensure_project_files(repo_path):
   """
   Create devbox.json, .envrc, .env, and .localbin/secrets in the repo.

   @param Path repo_path - canonical repo path
   """
   if not (repo_path / 'devbox.json').exists():
      _print_info(f'Running devbox init in {repo_path}')
      run_command(['devbox', 'init'], cwd=repo_path)
   else:
      _print_info('devbox.json already exists — keeping it')

   envrc = repo_path / '.envrc'
   if not envrc.exists():
      envrc.write_text(ENVRC_TEMPLATE)
      _print_info(f'Wrote {envrc}')

   env_file = repo_path / '.env'
   if not env_file.exists():
      env_file.write_text(ENV_TEMPLATE)
      _print_info(f'Wrote {env_file}')

   localbin = repo_path / '.localbin'
   localbin.mkdir(exist_ok=True)
   secrets = localbin / 'secrets'
   if not secrets.exists():
      secrets.write_text(SECRETS_TEMPLATE)
      secrets.chmod(0o755)
      _print_info(f'Wrote {secrets}')

   _print_info('Running devbox install (materializes .devbox and devbox.lock)')
   run_command(['devbox', 'install'], cwd=repo_path)
   run_command(['direnv', 'allow', str(repo_path)])


def find_repo_block(lines, name):
   """
   Find the line range of a repo entry inside the repos: block.

   @param list[str] lines - config file lines
   @param str name - repo key
   @return tuple(int, int, int) - (start, end, key_indent) or (-1, -1, 0)
   """
   in_repos = False
   repos_indent = -1
   start = -1
   key_indent = 0

   for i, line in enumerate(lines):
      stripped = line.rstrip('\n')
      if not stripped.strip():
         continue
      indent = len(stripped) - len(stripped.lstrip())

      if stripped.strip() == 'repos:':
         in_repos = True
         repos_indent = indent
         continue
      if not in_repos:
         continue
      if indent <= repos_indent:
         in_repos = False
         continue

      if start == -1 and stripped.strip() == f'{name}:':
         start = i
         key_indent = indent
         continue
      if start != -1 and indent <= key_indent:
         return (start, i, key_indent)

   if start != -1:
      return (start, len(lines), key_indent)
   return (-1, -1, 0)


def update_workspace_config(config_path, name, items):
   """
   Add symlink items to a repo entry in the config, preserving formatting.

   @param Path config_path - path to the workspace config
   @param str name - repo key
   @param list[str] items - symlink entries to ensure
   """
   lines = config_path.read_text().splitlines(keepends=True)
   start, end, key_indent = find_repo_block(lines, name)

   if start == -1:
      _exit_error(f'Repo "{name}" not found in {config_path} — add it first')

   child_indent = ' ' * (key_indent + 2)
   item_indent = ' ' * (key_indent + 4)
   block = lines[start:end]

   existing = [
      line.strip()[2:].strip() for line in block if line.strip().startswith('- ')
   ]
   missing = [item for item in items if item not in existing]
   if not missing:
      _print_info(f'All symlink entries already in {config_path}')
      return

   new_items = [f'{item_indent}- {item}\n' for item in missing]
   symlinks_idx = next(
      (i for i, line in enumerate(block) if line.strip() == 'symlinks:'), -1
   )

   if symlinks_idx == -1:
      insert_at = start + next(
         (i for i, line in enumerate(block) if line.strip().startswith('path:')), 0
      ) + 1
      lines[insert_at:insert_at] = [f'{child_indent}symlinks:\n'] + new_items
   else:
      last_item = start + symlinks_idx
      for i in range(symlinks_idx + 1, len(block)):
         if block[i].strip().startswith('- '):
            last_item = start + i
         elif block[i].strip():
            break
      lines[last_item + 1:last_item + 1] = new_items

   config_path.write_text(''.join(lines))
   _print_info(f'Added {", ".join(missing)} to {name} symlinks in {config_path}')


def ensure_global_gitignore():
   """Append dev environment patterns to the global git ignore file."""
   ignore_path = subprocess.run(
      ['git', 'config', '--global', 'core.excludesFile'],
      capture_output=True, text=True
   ).stdout.strip()

   path = Path(ignore_path).expanduser() if ignore_path else (
      Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')) / 'git' / 'ignore'
   )
   path.parent.mkdir(parents=True, exist_ok=True)
   content = path.read_text() if path.exists() else ''

   missing = [p for p in GLOBAL_IGNORE_PATTERNS if p not in content.splitlines()]
   if not missing:
      _print_info('Global git ignore already has all dev environment patterns')
      return

   prefix = '' if content.endswith('\n') or not content else '\n'
   header = '' if GLOBAL_IGNORE_HEADER in content else f'{GLOBAL_IGNORE_HEADER}\n'
   path.write_text(content + prefix + header + '\n'.join(missing) + '\n')
   _print_info(f'Added {len(missing)} patterns to {path}')


def ensure_direnv_whitelist(paths):
   """
   Whitelist path prefixes in direnv.toml so .envrc loads without manual allow.

   @param list[Path] paths - directory prefixes to whitelist
   """
   toml_path = (
      Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
      / 'direnv' / 'direnv.toml'
   )
   toml_path.parent.mkdir(parents=True, exist_ok=True)
   content = toml_path.read_text() if toml_path.exists() else ''

   wanted = [str(p) for p in paths if f'"{p}"' not in content]
   if not wanted:
      _print_info('direnv whitelist already covers these paths')
      return

   if '[whitelist]' in content and 'prefix' in content:
      _print_warning(
         f'direnv.toml already has a whitelist — add these prefixes manually: {wanted}'
      )
      return

   entries = ', '.join(f'"{p}"' for p in wanted)
   toml_path.write_text(content + f'\n[whitelist]\nprefix = [ {entries} ]\n')
   _print_info(f'Whitelisted {entries} in {toml_path}')


def cmd_init(name, config_path):
   """
   Set up a per-repo isolated dev environment (devbox + direnv + op secrets).

   @param str name - repo key or path
   @param str config_path - path to config file
   """
   path = Path(config_path)
   if not path.is_file():
      _exit_error(f'No config file found at {config_path}')

   config = load_config(config_path)
   repo_path = Path(resolve_repo(name, config))

   if not repo_path.is_dir():
      _exit_error(f'Repo path does not exist: {repo_path}')

   ensure_project_files(repo_path)
   update_workspace_config(path, name, DEVENV_SYMLINK_ITEMS)
   ensure_global_gitignore()
   ensure_direnv_whitelist([path.parent, repo_path])
   _print_info(
      f'Done. cd {repo_path} to activate; new workspaces get the '
      'environment automatically via symlinks'
   )


# -- Output helpers --------------------------------------------------

def _print_info(message):
   print(f"INFO {message}")


def _exit_error(message):
   print(f"ERROR {message}", file=sys.stderr)
   sys.exit(1)


def _print_warning(message):
   print(f"WARNING {message}", file=sys.stderr)


# -- CLI parsing -----------------------------------------------------

def build_parser():
   parser = argparse.ArgumentParser(
      prog='workspace',
      description='Workspace manager: git worktrees plus per-repo dev environments',
   )
   parser.add_argument(
      '--config', default=None,
      help=f'Path to config file (default: {DEFAULT_CONFIG_FILE})',
   )

   subparsers = parser.add_subparsers(dest='command')

   create_p = subparsers.add_parser('create', help='Create a worktree')
   create_p.add_argument('name', help='Repo name from config, or path')
   create_p.add_argument('branch', help='Branch to check out')
   create_p.add_argument(
      '--path', dest='custom_path', default='',
      help='Place worktree at <pwd>/<subdir>',
   )
   create_p.add_argument(
      '--symlink', nargs='?', const=True, default=True,
      help='Comma-separated symlink override (config symlinks are used by default)',
   )
   create_p.add_argument(
      '--no-symlink', dest='symlink', action='store_const', const=False,
      help='Do not symlink shared files into the new workspace',
   )
   create_p.add_argument(
      '--base-ref', dest='base_ref', default='',
      help='Ref to branch from when creating a new branch',
   )

   remove_p = subparsers.add_parser('remove', help='Remove a worktree')
   remove_p.add_argument(
      'name', help='Repo name/path, or "merged" to remove all merged',
   )
   remove_p.add_argument('branch', nargs='?', default=None)

   list_p = subparsers.add_parser('list', help='List worktrees')
   list_p.add_argument(
      'name', nargs='?', default=None,
      help='Repo name/path, or "merged"',
   )
   list_p.add_argument(
      '--configured', action='store_true',
      help='List all configured repos',
   )
   list_p.add_argument(
      '--all', dest='all_worktrees', action='store_true',
      help='Flat interactive list of every workspace by recent activity',
   )

   init_p = subparsers.add_parser(
      'init', help='Set up a per-repo dev environment (devbox + direnv + secrets)',
   )
   init_p.add_argument('name', help='Repo name from config, or path')

   install_p = subparsers.add_parser(
      'install', help='Install the worktree shell function and dependencies',
   )
   install_p.add_argument(
      '--shell', default='',
      help='Comma-separated shells (zsh, bash). Defaults to current shell.',
   )

   open_p = subparsers.add_parser(
      'open', help='Open a worktree in an editor',
   )
   open_p.add_argument('name', help='Repo name from config, or path')
   open_p.add_argument('branch', help='Branch whose worktree to open')
   open_p.add_argument(
      '--editor', default='',
      help='Editor command override (default: config or pycharm)',
   )

   diff_p = subparsers.add_parser(
      'diff', help='Open a worktree in a diff tool',
   )
   diff_p.add_argument('name', help='Repo name from config, or path')
   diff_p.add_argument('branch', help='Branch whose worktree to diff')
   diff_p.add_argument(
      '--diff', dest='diff_tool', default='',
      help='Diff tool override (default: config diff, then editor)',
   )

   meta_p = subparsers.add_parser(
      'meta', help='View or edit worktree metadata',
   )
   meta_p.add_argument('name', help='Repo name from config, or path')
   meta_p.add_argument('branch', help='Branch whose worktree to edit')
   meta_p.add_argument(
      '--title', default='',
      help='Set a title for the worktree',
   )
   meta_p.add_argument(
      '--notes', default='',
      help='Set notes for the worktree',
   )
   meta_p.add_argument(
      '--ticket', action='append', dest='tickets', default=[],
      help='Add a ticket URL (repeatable)',
   )
   meta_p.add_argument(
      '--link', action='append', dest='links', default=[],
      help='Add a link as label=url or url (repeatable)',
   )
   meta_p.add_argument(
      '--clear', action='store_true',
      help='Remove all metadata for this worktree',
   )

   return parser


def main(argv=None):
   parser = build_parser()
   args = parser.parse_args(argv)

   config_path = resolve_config_path(args.config)

   if not args.command:
      cmd_grid(config_path)
      return

   if args.command == 'create':
      symlink_flag = args.symlink is not False
      symlink_items = args.symlink if isinstance(args.symlink, str) else ''
      cmd_create(
         args.name, args.branch, symlink_flag,
         symlink_items, args.custom_path, config_path, args.base_ref,
      )

   elif args.command == 'remove':
      if args.name == 'merged':
         cmd_remove_merged(config_path)
      elif not args.branch:
         parser.error("remove requires <name> <branch> or 'merged'")
      else:
         cmd_remove(args.name, args.branch, config_path)

   elif args.command == 'list':
      if args.all_worktrees:
         cmd_list_interactive(config_path)
      else:
         cmd_list(args.name, config_path, args.configured)

   elif args.command == 'init':
      cmd_init(args.name, config_path)

   elif args.command == 'install':
      shells = [s.strip() for s in args.shell.split(',') if s.strip()]
      cmd_install(shells)

   elif args.command == 'open':
      cmd_open(args.name, args.branch, config_path, args.editor)

   elif args.command == 'diff':
      cmd_diff(args.name, args.branch, config_path, args.diff_tool)

   elif args.command == 'meta':
      cmd_meta(
         args.name, args.branch, config_path,
         args.title, args.notes, args.tickets, args.links, args.clear,
      )


if __name__ == '__main__':
   main()
