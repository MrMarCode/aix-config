---
name: skill-author
description: >
  Author, edit, and publish AIX skills. Draft locally in the current project,
  then promote to the public or private aix-config repo.
---

# Skill Author

Use this skill when the user wants to create, edit, or publish an AIX skill, or
when you notice a reusable pattern that should become a skill.

## Workflow

1. **Draft in the current project**
   - Run `aix-skill new <name> --description "..."` in the project where the
     skill will be tested.
   - This creates `skills/<name>/SKILL.md` and installs the skill locally with
     `aix add skill ./skills/<name>`.
   - The draft lives in the current project. It does not touch the public or
     private aix-config repos.
   - Edit `skills/<name>/SKILL.md` and run `aix-skill install` to refresh the
     local copy.

2. **Decide public or private**
   - Ask the user if the skill should go in the **public** or **private**
     aix-config repo.
   - Choose **private** if the skill references internal code, proprietary tools,
     organization-specific processes, credentials, or anything not appropriate
     for a public repo.
   - Choose **public** if it is a general coding, workflow, productivity, or
     agent-usage pattern.
   - If the user gives a direct answer, use the corresponding `--public` or
     `--private` flag.

3. **Publish**
   - Run `aix-skill push <name> --public` or `aix-skill push <name> --private`.
   - The script copies the skill to the local clone of the target repo, updates
     `ai.json`, commits and pushes to `master`, then runs `aix install`.
   - The local draft is removed from the current project after a successful push
     unless `--keep` is passed.

## Commands

- `aix-skill new <name> [--description "..."]` — create a local draft skill
- `aix-skill edit <name>` — open an existing draft in `$EDITOR`
- `aix-skill install` — re-install `ai.json` to refresh skills after edits
- `aix-skill push <name> --public|--private [--category <dir>]` — promote a
  draft to aix-config
- `aix-skill rm <name>` — remove a local draft
- `aix-skill status` — show local drafts and configured repo paths

## Configuration

Set these environment variables if the defaults are wrong:

- `AIX_PUBLIC_REPO` — path to public `aix-config` clone
  (auto-detected from the aix-skill script location)
- `AIX_PRIVATE_REPO` — path to private `aix-config` clone
  (auto-detected as a sibling of the public clone)
- `AIX_PROJECTS_DIR` — base directory for local aix-config clones; when set,
  overrides auto-detection for both public and private defaults
- `AIX_BIN` — `aix` binary name or path (default `aix`)
- `EDITOR` — editor used by `aix-skill edit`

Add `.../aix-config/skills/skill-author` to your `PATH` to run `aix-skill` from
anywhere.
