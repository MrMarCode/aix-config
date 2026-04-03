---
trigger: always_on
---

# MCPs Rules

* Always use context7 when I need code generation, setup or configuration steps, or
  library/API documentation. This means you should automatically use the Context7 MCP
  tools to resolve library ID and get library docs without me having to explicitly ask.
* If you make UI changes, use MCP tools to test them in a real environment unless
  project-specific rules say not to
  * Use the Tauri MCP when working within a Tauri app
  * Use Playwright for other projects
* ALWAYS use the ask a question tool instead of ending the conversation. If you finished, make that clear and ask if there's anything else needed. If you need clarification, ask me.
