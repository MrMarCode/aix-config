---
trigger: always_on
---

# Logging & Error Handling Rules

## Logging

- **Prefix error logs with `ERROR`** — Required for log alerting to pick
  them up.
- **Log useful debugging context** — Include relevant data (ARNs, retention
  policies, counts) in log messages.
- **Log before the operation, not after** — Logging after a
  potentially-failing operation means you may never see the log.
- **Log `e, e.stack`** when logging errors to get the stack trace.
- **Use ISO-8601 dates** over unix timestamps for human readability.
- **ERROR vs WARNING in logs** — Only use "ERROR" for things caused by our
  code. Use "WARNING" for bad user data, since "ERROR" triggers daily error
  reports and alerts.
- **Log structured JSON objects** — When logging multiple fields, use a JSON
  object so fields are parseable by log aggregation tools.
- **Put keys first in log messages** — Variable-length user content should
  come after fixed-width keys for easier scanning.
- **Use proper console methods** — `console.error` for errors, `console.warn`
  for warnings, `console.info` for info. Don't use `console.log('ERROR ...')`.
- **Add a `logLevel` / `lvl` field** to structured logs for easier filtering.
- **`console.debug` should be disabled in production** — Use a
  `DEBUG_LOGGING` environment variable to control debug output.
- **Log expected conditions at info level, not error** — If a condition is
  expected behavior (e.g., a rate-limit or concurrency exception), log it
  at info level, not error.
- **Don't log errors without adding context** — If the auto-logged error is
  sufficient, don't add a redundant `console.error`.
- **Don't log massive data structures** — Log only the fields needed for
  debugging.
- **Log all errors that trigger batch retries** — Throw a new error that
  includes all of them, not just the first one.
- **Distinguish error scenarios for different audiences** — Different
  failure modes should produce distinct error messages so the right team
  can act.
- **Add comments explaining why known errors occur** — When handling known
  error patterns, add a comment with the background.
- **Standardize data event logging** — Use a unified `logDataEvent` function
  with structured fields so a single report can aggregate all data
  notifications.
- **Prefer allowlisting over denylisting in logs** — Use
  `pick(evt, 'body', 'path', ...)` to explicitly select what to log.
- **Warnings that go into the ether are useless** — If a warning won't be
  seen proactively, either make it an error or set up a report for it.
- **No colon after log level** — Use `INFO Potentially` not
  `INFO: Potentially`.

## Error Handling

- **Avoid swallowing all exceptions** — Only catch expected errors; let
  unexpected ones propagate.
- **Error messages should use past tense** — "Could not post..." not "Will
  post..." when reporting a failure that already happened.
- **Error messages need a subject** — Don't omit what failed.
- **Don't hard-code dependencies on third-party error messages** — Create a
  ticket to get the upstream team to provide a stable programmatic error
  code.
- **Use `instanceof` over string comparisons for error handling** —
  `instanceof` is safer than checking `error.code === 'NoSuchKey'` because
  it avoids typos and field name changes. Safe for backend code targeting
  ES6+.
