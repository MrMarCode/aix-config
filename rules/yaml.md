---
trigger: glob
globs: "**/*.yml,**/*.yaml"
---

# YAML Style Rules

- **YAML array objects on separate lines** — Use the dash-on-its-own-line
  pattern for objects in arrays.
- **Collapse short object declarations** —
  `- { Name: year, Type: int }` is more scannable for simple key-value
  pairs.
- **Quote YAML strings with control characters** — Strings containing `:`
  should always be in single quotes.
- **Always indent objects in YAML** — Don't copy old unindented patterns
  from legacy services.
