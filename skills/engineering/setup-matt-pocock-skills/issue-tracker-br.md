# Issue tracker: Beads Rust (br)

Issues and specs for this repo are tracked with the [`br`](https://github.com/Dicklesworthstone/beads_rust) CLI — a local-first, non-invasive issue tracker storing tasks in SQLite with JSONL export for git collaboration.

## Setup

If `br` is not installed, install it:

```bash
curl -fsSL https://raw.githubusercontent.com/Dicklesworthstone/beads_rust/main/install.sh | bash
```

Initialize the workspace (creates `.beads/`):

```bash
br init
```

## Conventions

- Issues are created with `br create "Title" --type <type> --priority <n> --description "..."`
- Each issue gets a unique ID like `br-a1b2c3`
- Triage state is managed via labels: `br label add <id> <label>`
- Comments are added with `br comments add <id> "text"`
- Dependencies are managed with `br dep add <child> <parent>`
- Status transitions: `br update <id> --status <open|in_progress|closed>`

## When a skill says "publish to the issue tracker"

Create a new issue with `br create`. Use `--type` to categorize (bug, feature, task, etc.) and `--priority` for urgency.

## When a skill says "fetch the relevant ticket"

Use `br show <id>` to read an issue, or `br list` / `br search "text"` to find issues.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a `br` issue labelled `wayfinder:map`.

- **Map**: `br create "Map: <effort>" --type task`, then `br label add <map-id> wayfinder:map`
- **Child ticket**: `br create "<question>" --type <research|prototype|grilling|task>`, then `br dep add <child-id> <map-id>`
- **Blocking**: `br dep add <child-id> <blocker-id>` — a ticket is unblocked when every blocker is closed
- **Frontier**: `br ready` — shows issues that are open, not blocked, not deferred
- **Claim**: `br update <id> --status in_progress --assignee "$(git config user.email)"`
- **Resolve**: `br comments add <id> "<answer>"`, then `br close <id> --reason "<summary>"`, then append a context pointer to the map issue's comments
