---
trigger: glob
globs: "**/*.sh,**/*.yml,**/*.yaml"
---

# Shell Script Rules

- **Shell scripts need interpreter directives** (shebang lines).
- **Shell commands should include `|| exit 1`** for error handling.
- **Use `mktemp` instead of hardcoded paths** in shell scripts.
- **Avoid `rm -rf "${VAR}"` in bash** — Explicitly `rm` individual files and
  `rmdir` directories.
- **Avoid bash arrays** — They are not portable across shells.
- **Use case statements for arg parsing** — Not hacky positional argument
  checks.
- **Exit with non-zero on failure** — `exit 1` when something fails.
- **Echo destructive commands for review** — Have the script echo the exact
  commands, put them in the MR for review, then copy-paste to execute.
