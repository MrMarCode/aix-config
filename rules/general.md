---
trigger: always_on
---

# General Rules

IMPORTANT: if your unsure about how a command or library works first look it up, then create a simple environment to test it and run it using run-box.

## Core Principles

   * Always take a declarative approach when writing code
   * Prioritize readability: avoid deep nesting, break complex conditions into named variables/functions
   * Consistent formatting that represents logical structure
   * Follow existing patterns in codebase
   * Separate formatting-only changes from functional changes
   * Avoid nested if statements at all costs, the goal is declarative, composable, clear code
   * Summarize only when requested!
   * Write functions that are easily unit testable.

## Critical Rules (Always Enforce)

   1. When refactoring, never remove functionality unless specifically directed to do so
   2. When you use or answer questions about an API, library, or command, query context7
   3. Keep your answers brief and to the point
   4. LIMIT your use of log messages. If you must log something, include it all in one log message, DO NOT split it up
   5. LIMIT your use of comments
   6. Types should exist in the file they are used in and exported if needed elsewhere.
   7. Whenever you find an answer from an external source (such as an mcp server, or the web),
      ALWAYS include a link to your reference.
      E.g: `[State machines have a default timeout of infinite.](https://docs.aws...)`

## Code Quality & Design

   * Readability over cleverness — Add intermediate variables to reduce
     mental load.
   * Single Responsibility Principle — Functions should have one clear
     responsibility. If a function name no longer describes what it does,
     split it.
   * Functions should not have side effects unrelated to their name —
     `hasFileBeenProcessed()` should not also delete the source object.
   * Fail fast — Validate inputs early, at the public function boundary,
     not deep in private helpers.
   * No nested ternaries — Keep ternary usage simple and readable.
   * Remove unused code — Don't comment out code; version control
     preserves history.
   * Prefer functional style — Use `.map()`, `.filter()`, native array
     methods, or toolbox utilities over imperative loops.
   * Prefer simpler native methods — `keys(obj).sort()` is clearer than
     `sortBy(keys(obj), identity)`.
   * Add parentheses around `||` in compound conditions — Reduces mental
     load; devs don't have to remember operator precedence.
   * Don't compare objects with `JSON.stringify` — It's unreliable due to
     key ordering.
   * Avoid recursive pagination — Recursive calls for paginated API
     results can cause stack overflows. Use iterative loop/nextTick
     patterns instead.
   * Avoid premature abstraction — Don't create helper functions that just
     wrap one or two external calls.
   * Don't roll your own templating syntax — Use established libraries.
   * Parallelize independent async calls — Use `Promise.all` when calls
     don't depend on each other.
   * Start async work early, await late — For fire-and-forget API calls,
     start the promise at the top and await it at the end.
   * Only fetch data when needed — Don't fetch data "for simplicity" if
     it's only needed sometimes.
   * Extract magic numbers into named constants —
     `MIN_TIME_FOR_TEXT_ANALYSIS_MILLIS` not `30`.
   * Co-locate related config — When filters and matchers must stay in
     sync, put them in the same config object.
   * Use data-driven iteration over hard-coded switches.
   * Don't parse your own data structures as strings — Build the data
     natively where it's needed.
   * Make properties readonly when they shouldn't change after
     construction.
   * Standardize function interfaces — If `writeContentDoc` takes specific
     params, `readContentDoc` should follow the same pattern.
   * Use `isEmpty` consistently — Replace `if (!x)` checks with
     `isEmpty(x)` for checking array/object emptiness.
   * Separate business logic from event handling — Business logic classes
     shouldn't know about the event type that triggered them.
   * Reduce cyclomatic complexity — Use underscore chains with comments
     instead of nested loops/conditionals.
   * Be safe with multibyte characters — `String.slice()` can split
     multibyte characters. Use spread operator `[...str]` for
     character-safe operations.
   * Keep library APIs future-proof — Even if a method doesn't need to be
     async right now, keep it async if the API contract should allow for
     it.
   * Export library functionality, not raw data — Export helpful functions
     like `getMaxItemCount(category, subcategory)`.
   * Whitelist options rather than passing through entire objects.
   * Don't default values in two places — Pick one authoritative location
     for defaults.
   * Sanitize inputs — Don't assume current data will always be clean.
   * Put data transformations in the right layer — Bad data should be
     cleaned in a transformer, not in ad-hoc code.
   * Separate race condition solutions from batching optimizations —
     Locking/conditional writes solve race conditions. Queues with delays
     solve batching/deduplication.
   * Use conditional writes (`updateUUID`) for transactional consistency.

## Architecture & Event Design

   * Events belong to the emitting service — A service emits an event
     and doesn't care who listens. The emitter "owns" the event type.
   * Keep service-specific types in the owning service — Don't move
     types to `model/shared` unless genuinely shared between backend and
     frontend. This applies to TypeScript types and interfaces too —
     co-locate them with the service or module that owns the concept.
   * Validate implicit type contracts — If an external event is
     implicitly passed through a workflow, ensure the internal contract
     stays in sync.
   * Don't pollute core model interfaces — Extend the interface at the
     event level rather than adding fields to `toPlainObject()`.
   * Rename methods to reflect their actual purpose —
     `toPlainObject()` → `toMenuActivationEvent()`.

## Cache Design

   * Expose structured cache key builders — Provide an enum of entry
     types, version numbers, and separate unhashed/hashed key parts.
   * Tie storage TTL to validity TTL — Don't store data for 90 days if
     it's only valid for 7.
   * Never put unsanitized user input in unhashed key parts — User
     search queries go in `hashedParts`.
   * Cache negative results — If a feature API returns "not enabled,"
     cache that result.
   * Don't fetch config on every request if it doesn't change
     frequently — cache it.
   * Set connect timeouts on all external service calls — don't rely on
     defaults.
   * Use data to justify timeouts — Check latency metrics before setting
     timeouts.

## Data Handling

   * Centralize normalization in model classes —
     `Language.normalize_locale()` should be the single source of truth.
   * Sanitize input early — Normalize query string params at the entry
     point.
   * Regex should be precise — Language codes are 1-3 characters, not
     "one or more" (`{1,3}` not `+`).
   * Use `/u` flag on regex for multi-lingual text.
   * Account for invisible Unicode characters — Non-breaking spaces
     (`\u00a0`), zero-width joiners, and locale-specific formatting
     characters can break string comparison and parsing.
   * Avoid smart quotes in user-facing strings.

## Operational Practices

   * Defensive coding for destructive operations — Code that deletes
     data should be as simple as possible.
   * Document "gotchas" so they don't recur.
   * Clean up related data, not just primary records — When deleting
     records, also clean up related table references.

## Thinking & Reasoning

   * "Programming is science, not art" — Think through decisions
     rigorously.
   * Explain your thinking — Reviewers ask "please explain your thinking
     on this" to ensure decisions are deliberate.
   * Understand existing code before changing it — Know what
     functionality exists and why before refactoring.
   * Consider the pros and cons of changes — Don't make changes without
     thinking through implications.
   * Challenge your own assumptions — Before asserting something can't
     be done, check the docs.
   * Think through the design before coding — List endpoints, behaviors,
     operations, overlaps, and data needs.
   * Verify assumptions with data — Query production data to confirm
     rather than guessing.

## Conversation Style

   * When responding, keep things to the point.
   * Respond directly without preamble.
   * When referencing specific lines in a file, ALWAYS include a link to it using the format: [filename](cci:1://file:///filepath...:153:0-171:0)
