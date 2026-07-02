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
  $SCRIPT_NAME create <name|path> <branch> [--path <subdir>] [--symlink [items]]
  $SCRIPT_NAME remove <name|path> <branch>
  $SCRIPT_NAME remove merged
  $SCRIPT_NAME list [name|path]
  $SCRIPT_NAME list merged

<name> is a repo key from $CONFIG_FILE, or a path to a git repo.

Options:
  --path <subdir>    Place worktree at <pwd>/<subdir> instead of derived name
  --symlink          Symlink files from source repo (uses config list)
  --symlink 'a,b'    Override symlink list with comma-separated items

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
   local custom_path="$5"

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
   if [ -n "$custom_path" ]; then
      dir_name="$custom_path"
   else
      dir_name="$(_safe_branch_dir "$branch")"
   fi
   local worktree_dir
   worktree_dir="$(pwd)/$dir_name"

   if [ -e "$worktree_dir" ]; then
      _err "Path already exists: $worktree_dir"
   fi

   local parent_dir
   parent_dir="$(dirname "$worktree_dir")"
   mkdir -p "$parent_dir"

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

_worktree_path_for_branch() {
   local repo_path="$1"
   local branch="$2"
   local wt_path=""
   local wt_branch=""
   local line
   while IFS= read -r line; do
      case "$line" in
         "worktree "*) wt_path="${line#worktree }" ;;
         "branch refs/heads/"*) wt_branch="${line#branch refs/heads/}" ;;
         "")
            if [ -n "$wt_path" ] && [ "$wt_branch" = "$branch" ]; then
               echo "$wt_path"
               return 0
            fi
            wt_path=""
            wt_branch=""
            ;;
      esac
   done < <(git -C "$repo_path" worktree list --porcelain; echo "")
   return 1
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

   local worktree_dir
   worktree_dir="$(_worktree_path_for_branch "$repo_path" "$branch" || true)"

   if [ -z "$worktree_dir" ]; then
      local dir_name
      dir_name="$(_safe_branch_dir "$branch")"
      worktree_dir="$(pwd)/$dir_name"
      if [ ! -d "$worktree_dir" ]; then
         _err "No worktree found for branch '$branch' in $repo_path"
      fi
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

_default_branch() {
   local repo_path="$1"
   local config_file="$2"
   local name="$3"

   if [ -n "$config_file" ] && [ -n "$name" ]; then
      local override
      override="$(yq -r ".repos.\"$name\".default_branch // \"\"" "$config_file" 2>/dev/null)"
      if [ -n "$override" ]; then
         echo "$override"
         return 0
      fi
   fi

   local head_ref
   head_ref="$(git -C "$repo_path" symbolic-ref --quiet refs/remotes/origin/HEAD 2>/dev/null || true)"
   if [ -n "$head_ref" ]; then
      echo "${head_ref#refs/remotes/origin/}"
      return 0
   fi

   local b
   for b in master main; do
      if git -C "$repo_path" show-ref --verify --quiet "refs/remotes/origin/$b"; then
         echo "$b"
         return 0
      fi
   done
   return 1
}

_is_merged_to_default() {
   local repo_path="$1"
   local branch="$2"
   local default_branch="$3"
   local hit
   hit="$(git -C "$repo_path" log "origin/$default_branch" --merges -F \
      --grep="$branch" -n 1 --format=%H 2>/dev/null || true)"
   [ -n "$hit" ]
}

# Emits tab-separated: <repo_name>\t<branch>\t<worktree_path>\t<repo_path>
_list_merged_worktrees() {
   _require_yq

   local config_file
   config_file="$(_resolve_config)" || _err "No config file found at $CONFIG_FILE"

   local repos
   repos="$(yq -r '.repos | to_entries[] | .key' "$config_file")"

   local name
   while IFS= read -r name; do
      [ -z "$name" ] && continue

      local repo_path
      repo_path="$(yq -r ".repos.\"$name\".path // \"\"" "$config_file")"
      [ -z "$repo_path" ] && continue
      if [ ! -d "$repo_path/.git" ] && [ ! -f "$repo_path/.git" ]; then
         continue
      fi

      local default_branch
      default_branch="$(_default_branch "$repo_path" "$config_file" "$name")" || {
         _warn "Cannot determine default branch for $repo_path — skipping"
         continue
      }

      local main_worktree
      main_worktree="$(git -C "$repo_path" rev-parse --show-toplevel 2>/dev/null || echo "")"

      local wt_path=""
      local wt_branch=""
      local line
      while IFS= read -r line; do
         case "$line" in
            "worktree "*)
               wt_path="${line#worktree }"
               ;;
            "branch refs/heads/"*)
               wt_branch="${line#branch refs/heads/}"
               ;;
            "")
               if [ -n "$wt_path" ] && [ -n "$wt_branch" ] \
                     && [ "$wt_path" != "$main_worktree" ]; then
                  if _is_merged_to_default "$repo_path" "$wt_branch" "$default_branch"; then
                     printf "%s\t%s\t%s\t%s\n" "$name" "$wt_branch" "$wt_path" "$repo_path"
                  fi
               fi
               wt_path=""
               wt_branch=""
               ;;
         esac
      done < <(git -C "$repo_path" worktree list --porcelain; echo "")
   done <<< "$repos"
}

cmd_list_merged() {
   local merged
   merged="$(_list_merged_worktrees)"
   if [ -z "$merged" ]; then
      echo "No merged worktrees found"
      return 0
   fi
   printf "%s\n" "$merged" | awk -F'\t' '{printf "%s  %s  %s\n", $1, $2, $3}' \
      | column -t
}

cmd_remove_merged() {
   local merged
   merged="$(_list_merged_worktrees)"
   if [ -z "$merged" ]; then
      echo "No merged worktrees found"
      return 0
   fi

   local name branch wt_path repo_path
   while IFS=$'\t' read -r name branch wt_path repo_path; do
      [ -z "$wt_path" ] && continue
      echo "Removing $wt_path (repo: $name, branch: $branch)"
      git -C "$repo_path" worktree remove "$wt_path" --force
   done <<< "$merged"
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
      CUSTOM_PATH=""

      while [ $# -gt 0 ]; do
         case "$1" in
            --symlink)
               SYMLINK_FLAG="true"
               if [ $# -gt 1 ] && [[ "$2" != --* ]]; then
                  SYMLINK_ITEMS="$2"
                  shift
               fi
               ;;
            --path)
               [ $# -lt 2 ] && _err "--path requires a value"
               CUSTOM_PATH="$2"
               shift
               ;;
            *) _err "Unknown option: $1" ;;
         esac
         shift
      done

      cmd_create "$NAME" "$BRANCH" "$SYMLINK_FLAG" "$SYMLINK_ITEMS" "$CUSTOM_PATH"
      ;;
   remove)
      [ $# -lt 1 ] && _usage
      if [ "$1" = "merged" ]; then
         cmd_remove_merged
      else
         [ $# -lt 2 ] && _usage
         cmd_remove "$1" "$2"
      fi
      ;;
   list)
      if [ $# -lt 1 ]; then
         cmd_list_all
      elif [ "$1" = "merged" ]; then
         cmd_list_merged
      else
         cmd_list "$1"
      fi
      ;;
   -h|--help) _usage ;;
   *) _err "Unknown command: $COMMAND" ;;
esac
