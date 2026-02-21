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
- **Commit type matters** — `style:` not `fix:` for whitespace-only changes.
  Follow Angular commit conventions.
- **Squash closely related commits** into one — Makes seeing the "unit" of
  work easier in the log.

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
