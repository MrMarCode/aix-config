---
trigger: glob
globs: "**/package.json"
---

# NPM & Dependency Management Rules

- **Exact version specifiers in `package.json`** — No `^` or `~`.
- **Don't commit dist folders** — Find a proper fix for build issues.
- **Test dependency upgrades across multiple services**.
- **Three-space indentation for new `package.json` files**.
