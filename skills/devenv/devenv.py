#!/usr/bin/env python3
"""Per-repo isolated dev environment setup (devbox + direnv + op secrets)."""

import argparse
import os
import subprocess
import sys
from pathlib import Path

try:
   import yaml
except ImportError:
   print('ERROR pyyaml is required (python3 -c "import yaml" failed)', file=sys.stderr)
   sys.exit(1)

SYMLINK_ITEMS = ['devbox.json', 'devbox.lock', '.envrc', '.env', '.devbox', '.localbin']

GLOBAL_IGNORE_HEADER = '# devenv skill — per-repo dev environment files (never committed)'
GLOBAL_IGNORE_PATTERNS = [
   'devbox.json',
   'devbox.lock',
   '.devbox/',
   '.direnv/',
   '.envrc',
   '.env',
   '.localbin/',
]

ENVRC_TEMPLATE = '''# Managed by the devenv skill. Never tracked in git (global ignore).
eval "$(devbox generate direnv --print-envrc)"

# Plain values load into the environment; op:// references stay literal
# until you run `secrets`.
dotenv_if_exists .env

PATH_add .localbin
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


def _print_info(msg):
   print(f'INFO {msg}')


def _print_warning(msg):
   print(f'WARNING {msg}', file=sys.stderr)


def _fail(msg):
   print(f'ERROR {msg}', file=sys.stderr)
   sys.exit(1)


def resolve_config_path(cli_config):
   """
   Resolve the .worktree.yaml path.

   @param str cli_config - --config value or empty
   @return Path - config file path
   """
   candidates = [
      cli_config,
      os.environ.get('WORKTREE_CONFIG', ''),
      str(Path.cwd() / '.worktree.yaml'),
   ]
   existing = [Path(c) for c in candidates if c and Path(c).is_file()]

   if not existing:
      _fail('No .worktree.yaml found — pass --config or set WORKTREE_CONFIG')
   return existing[0]


def resolve_repo_path(name, config):
   """
   Resolve a repo name or direct path to an absolute repo path.

   @param str name - repo key in config, or a filesystem path
   @param dict config - parsed .worktree.yaml
   @return Path - absolute repo path
   """
   repo = config.get('repos', {}).get(name, {})
   if repo.get('path'):
      return Path(repo['path'])

   direct = Path(name).expanduser()
   if (direct / '.git').exists():
      return direct.resolve()

   _fail(f'Repo "{name}" not in config and not a git repo path')


def run(cmd, cwd=None):
   """
   Run a command, failing loudly on error.

   @param list[str] cmd - command and args
   @param Path cwd - working directory (optional)
   """
   result = subprocess.run(cmd, cwd=cwd)

   if result.returncode != 0:
      _fail(f'Command failed: {" ".join(cmd)}')


def ensure_project_files(repo_path):
   """
   Create devbox.json, .envrc, .env, and .localbin/secrets in the repo.

   @param Path repo_path - canonical repo path
   """
   if not (repo_path / 'devbox.json').exists():
      _print_info(f'Running devbox init in {repo_path}')
      run(['devbox', 'init'], cwd=repo_path)
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
   run(['devbox', 'install'], cwd=repo_path)
   run(['direnv', 'allow', str(repo_path)])


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


def update_worktree_config(config_path, name, items):
   """
   Add symlink items to a repo entry in .worktree.yaml, preserving formatting.

   @param Path config_path - path to .worktree.yaml
   @param str name - repo key
   @param list[str] items - symlink entries to ensure
   """
   lines = config_path.read_text().splitlines(keepends=True)
   start, end, key_indent = find_repo_block(lines, name)

   if start == -1:
      _fail(f'Repo "{name}" not found in {config_path} — add it first')

   child_indent = ' ' * (key_indent + 2)
   item_indent = ' ' * (key_indent + 4)
   block = lines[start:end]

   existing = [
      line.strip()[2:].strip() for line in block if line.strip().startswith('- ')
   ]
   missing = [item for item in items if item not in existing]
   if not missing:
      _print_info('All symlink entries already in .worktree.yaml')
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
   """Append devenv patterns to the global git ignore file."""
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
      _print_info('Global git ignore already has all devenv patterns')
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


def cmd_init(name, cli_config):
   """
   Full setup for one repo.

   @param str name - repo key or path
   @param str cli_config - --config override or empty
   """
   config_path = resolve_config_path(cli_config)
   config = yaml.safe_load(config_path.read_text()) or {}
   repo_path = resolve_repo_path(name, config)

   if not repo_path.is_dir():
      _fail(f'Repo path does not exist: {repo_path}')

   ensure_project_files(repo_path)
   update_worktree_config(config_path, name, SYMLINK_ITEMS)
   ensure_global_gitignore()
   ensure_direnv_whitelist([config_path.parent, repo_path])
   _print_info(
      f'Done. cd {repo_path} to activate; new worktrees created with '
      '--symlink get the environment automatically'
   )


def main():
   parser = argparse.ArgumentParser(description='Per-repo dev environment setup')
   sub = parser.add_subparsers(dest='command', required=True)

   init_parser = sub.add_parser('init', help='Set up devbox+direnv for a repo')
   init_parser.add_argument('name', help='Repo name from .worktree.yaml, or a path')
   init_parser.add_argument('--config', default='', help='Path to .worktree.yaml')

   args = parser.parse_args()
   if args.command == 'init':
      cmd_init(args.name, args.config)


if __name__ == '__main__':
   main()
