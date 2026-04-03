#!/bin/bash
set -euo pipefail

CONFIG_FILE="${WORKTREE_CONFIG:-.worktree.yaml}"
SCRIPT_NAME="$(basename "$0")"

_err() {
   echo "ERROR $1" >&2
   exit 1
}

_warn() {
   echo "WARNING $1" >&2
}

_require_yq() {
   command -v yq >/dev/null 2>&1 || _err "yq is required but not installed"
}

_resolve_config() {
   if [ -f "$CONFIG_FILE" ]; then
      echo "$CONFIG_FILE"
      return 0
   fi
   return 1
}

_safe_branch_dir() {
   echo "$1" | sed 's/[\/]/-/g'
}

_resolve_repo() {
   local name="$1"
   local config_file="$2"

   if [ -n "$config_file" ]; then
      local repo_path
      repo_path="$(yq -r ".repos.\"$name\".path // \"\"" "$config_file")"
      if [ -n "$repo_path" ]; then
         echo "$repo_path"
         return 0
      fi
   fi

   if [ -d "$name/.git" ] || [ -f "$name/.git" ]; then
      echo "$name"
      return 0
   fi

   if [ -n "$config_file" ]; then
      _err "'$name' not found in config and is not a path to a git repo. Check repos in $config_file"
   fi
   _err "'$name' is not a path to a git repo and no config file found"
}

_resolve_symlinks() {
   local name="$1"
   local config_file="$2"
   local inline_override="$3"

   if [ -n "$inline_override" ]; then
      echo "$inline_override" | tr ',' '\n'
      return 0
   fi

   if [ -z "$config_file" ]; then
      return 0
   fi

   local repo_symlinks
   repo_symlinks="$(yq -r ".repos.\"$name\".symlinks // [] | .[]" "$config_file" 2>/dev/null)"
   if [ -n "$repo_symlinks" ]; then
      echo "$repo_symlinks"
      return 0
   fi

   yq -r '.default.symlinks // [] | .[]' "$config_file" 2>/dev/null
}

_usage() {
   cat <<EOF
Usage:
  $SCRIPT_NAME create <name|path> <branch> [--symlink [items]]
  $SCRIPT_NAME remove <name|path> <branch>
  $SCRIPT_NAME list [name|path]

<name> is a repo key from $CONFIG_FILE, or a path to a git repo.

Options:
  --symlink          Symlink files from source repo (uses config list)
  --symlink 'a,b'   Override symlink list with comma-separated items

Environment:
  WORKTREE_CONFIG    Path to config file (default: .worktree.yaml)
EOF
   exit 1
}

cmd_create() {
   local name="$1"
   local branch="$2"
   local symlink_flag="$3"
   local symlink_items="$4"

   _require_yq

   local config_file=""
   if _resolve_config >/dev/null 2>&1; then
      config_file="$(_resolve_config)"
   else
      _warn "No config file found at $CONFIG_FILE — symlinking disabled"
   fi

   local repo_path
   repo_path="$(_resolve_repo "$name" "$config_file")"

   if [ ! -d "$repo_path/.git" ] && [ ! -f "$repo_path/.git" ]; then
      _err "Git repo not found at: $repo_path"
   fi

   local dir_name
   dir_name="$(_safe_branch_dir "$branch")"
   local worktree_dir
   worktree_dir="$(pwd)/$dir_name"

   if [ -d "$worktree_dir" ]; then
      _err "Directory already exists: $worktree_dir"
   fi

   if git -C "$repo_path" show-ref --verify --quiet "refs/heads/$branch" \
      || git -C "$repo_path" show-ref --verify --quiet "refs/remotes/origin/$branch"; then
      git -C "$repo_path" worktree add "$worktree_dir" "$branch"
   else
      git -C "$repo_path" worktree add -b "$branch" "$worktree_dir"
   fi

   if [ "$symlink_flag" = "true" ] && [ -n "$config_file" ]; then
      local symlinks
      symlinks="$(_resolve_symlinks "$name" "$config_file" "$symlink_items")"

      if [ -n "$symlinks" ]; then
         while IFS= read -r item; do
            [ -z "$item" ] && continue
            local source="$repo_path/$item"
            local target="$worktree_dir/$item"

            if [ ! -e "$source" ]; then
               _warn "$item not found at $source — skipping"
               continue
            fi

            local target_dir
            target_dir="$(dirname "$target")"
            mkdir -p "$target_dir"
            ln -s "$(realpath "$source")" "$target"
         done <<< "$symlinks"
      fi
   elif [ "$symlink_flag" = "true" ] && [ -z "$config_file" ]; then
      if [ -n "$symlink_items" ]; then
         while IFS= read -r item; do
            [ -z "$item" ] && continue
            local source="$repo_path/$item"
            local target="$worktree_dir/$item"

            if [ ! -e "$source" ]; then
               _warn "$item not found at $source — skipping"
               continue
            fi

            local target_dir
            target_dir="$(dirname "$target")"
            mkdir -p "$target_dir"
            ln -s "$(realpath "$source")" "$target"
         done <<< "$(echo "$symlink_items" | tr ',' '\n')"
      fi
   fi

   echo "$worktree_dir"
}

cmd_remove() {
   local name="$1"
   local branch="$2"

   _require_yq

   local config_file=""
   if _resolve_config >/dev/null 2>&1; then
      config_file="$(_resolve_config)"
   fi

   local repo_path
   repo_path="$(_resolve_repo "$name" "$config_file")"

   local dir_name
   dir_name="$(_safe_branch_dir "$branch")"
   local worktree_dir
   worktree_dir="$(pwd)/$dir_name"

   if [ ! -d "$worktree_dir" ]; then
      _err "Worktree directory not found: $worktree_dir"
   fi

   git -C "$repo_path" worktree remove "$worktree_dir" --force
   echo "Removed $worktree_dir"
}

cmd_list_all() {
   _require_yq

   local config_file=""
   if _resolve_config >/dev/null 2>&1; then
      config_file="$(_resolve_config)"
   else
      _err "No config file found at $CONFIG_FILE"
   fi

   yq -r '.repos | to_entries[] | .key + "\t" + .value.path' "$config_file"
}

cmd_list() {
   local name="$1"

   _require_yq

   local config_file=""
   if _resolve_config >/dev/null 2>&1; then
      config_file="$(_resolve_config)"
   fi

   local repo_path
   repo_path="$(_resolve_repo "$name" "$config_file")"

   git -C "$repo_path" worktree list
}

if [ $# -lt 1 ]; then
   _usage
fi

COMMAND="$1"
shift

case "$COMMAND" in
   create)
      [ $# -lt 2 ] && _usage
      NAME="$1"
      BRANCH="$2"
      shift 2

      SYMLINK_FLAG="false"
      SYMLINK_ITEMS=""

      while [ $# -gt 0 ]; do
         case "$1" in
            --symlink)
               SYMLINK_FLAG="true"
               if [ $# -gt 1 ] && [[ "$2" != --* ]]; then
                  SYMLINK_ITEMS="$2"
                  shift
               fi
               ;;
            *) _err "Unknown option: $1" ;;
         esac
         shift
      done

      cmd_create "$NAME" "$BRANCH" "$SYMLINK_FLAG" "$SYMLINK_ITEMS"
      ;;
   remove)
      [ $# -lt 2 ] && _usage
      cmd_remove "$1" "$2"
      ;;
   list)
      if [ $# -lt 1 ]; then
         cmd_list_all
      else
         cmd_list "$1"
      fi
      ;;
   -h|--help) _usage ;;
   *) _err "Unknown command: $COMMAND" ;;
esac
