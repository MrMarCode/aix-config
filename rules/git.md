---
trigger: always_on
---

# Git & Merge Request Rules

## Commit Messages

- **Commit messages must explain "why"** — Use imperative mood: mental prefix
  "If applied, this commit will..."
- **Remove filler from commit messages** — e.g., remove "The motivation
  behind making this change is that".
- **Separate commits for separate concerns** — Keep generated file changes in
  their own commit, separate from code changes.
- **Commit messages must reference ticket numbers** — Always reference a PBI
  or feature ticket number.
- **Commit message titles should not be redundant** — e.g., "fix: fix
  suggestion parsing" is bad.
- **Squash closely related commits** into one — Makes seeing the "unit" of
  work easier in the log.

## Commit Message Format

- **Format**: `type: subject` (e.g., `fix: permissions for test files (#12345)`)
- **Allowed types** and explanations:
  - **build**: changes that affect the build system or external dependencies.
  - **chore**: Other changes that don't modify src or test files. Also used for releases.
  - **ci**: Changes to our CI configuration files and scripts.
  - **config**: Changes to how a service runs.
  - **docs**: Changes only affecting documentation.
  - **feat**: A new feature.
  - **fix**: Bug fix.
  - **sub(type)**: any smaller chunk of a defined type. ie: sub(feat) some small part of feature
  - **perf**: A code change that improves performance.
  - **refactor**: A code change that neither fixes a bug nor adds a feature.
  - **revert**: Reverts a previous commit.
  - **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing smi-colons, etc)
  - **test**: Adding missing tests or correcting existing tests.
- **Nothing else before the colon** — No scopes, no extra words.
  Just the type keyword.

## Merge Request Practices

- **Update MR title** when commit message changes.
- **Reviewers resolve discussions**, not the author.
- **Don't push to an MR that is "in review"** — Creates extra diff noise.
- **Don't put conversation in MR descriptions** — Title and description
  become part of the commit.
- **Delete source branch after merge**.
- **Self-review before sending for review** — "Did you review this yourself
  before sending it to me?"
- **Mark dependent MRs as WIP/draft** — If an MR can't be merged until
  another ships, mark it as draft to prevent accidental merging.
- **Keep scope focused** — Pull out-of-scope changes into separate MRs.
- **Provide context in MR comments** — When removing TODOs, explain why each
  one is being removed.
