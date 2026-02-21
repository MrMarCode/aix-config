---
trigger: always_on
---

# Testing Rules

- **Keep test data in the test file** — Don't use separate JSON fixture
  files; generate data programmatically. "A function or two is far easier to
  manage than 74 objects."
- **Setup fake data within the `it` block** — Place fake data in the test
  that uses it.
- **Extract shared constants** to reduce test fragility.
- **Test edge cases** — Empty inputs, disabled states, boundary conditions.
- **Test idempotency** — Verify that running an operation twice produces the
  same result.
- **Separate `it` blocks for each case** — Don't combine multiple test cases
  in one `it` block.
- **Use Sinon's fake timers** over mocking time libraries directly.
- **Use `calledWithExactly`** for precise stub assertions.
- **Only stub what's necessary** — When testing a public function, only stub
  the direct dependencies it calls.
- **Test that packaging changes work across all services** before merging.
- **Validate invalid inputs** — Functions that return valid data must check
  for invalid inputs.
- **Fix the source, not the test** — When a function returns the wrong type,
  fix the function, not the test expectations.
- **Don't base tests on total call counts** — Basing tests on `console.log`
  call counts is fragile. Return a value and assert on that instead.
- **Use `resetHistory`** on Sinon stubs to get per-test invocation counts.
- **Write comparison scripts** for API refactors to validate old vs. new
  behavior.
- **Ensure tests run in CI** — Verify tests are included in the CI pipeline.
- **Use `AssertionError`** with `expected`/`actual` for clear test failure
  output.
- **Report all failures, not just the first** — Collect all errors before
  asserting.
- **Create shared test helpers** — e.g.,
  `makeFakeMasterLanguage(overrides)` with `Partial<Language>` parameter.
- **Place test helpers in shared locations** — e.g.,
  `lib/tests/language-helpers.ts`.
- **Add tests for invisible behaviors** — "When this breaks it isn't very
  visible so the tests are very important."
- **Provide examples of test failure output** — Show what failures look like
  so reviewers can evaluate readability.
- **Abstract date logic for testability** — Extract date manipulation into
  separate testable functions.
- **Use made-up IDs in test examples** — Don't use real user IDs in test
  data.
- **Test edge cases like unsorted arrays** — If data from source database isn't
  guaranteed to be sorted, add tests with unsorted input.
- **Reduce test logic complexity** — When tests have too much logic, bugs
  hide in the tests themselves. Make test data explicit.
- **Use clock functions in tests instead of tiny TTLs** — Don't use `1ms`
  TTL to test cache expiration. Use `sinon.useFakeTimers()`.
- **Validate API responses against JSON schemas in integration tests**.
- **Write unit tests for complex, critical, easy-to-test functions** —
  Functions that are (a) complex to reason about, (b) critical to system
  correctness, and (c) don't depend on external services should always have
  unit tests.
- **Use `rewire` for testing module-level constants**.
- **Reset global state after tests** — When modifying env vars or global
  state in tests, always restore the original value in an `afterEach` block.
- **Tighten regexes** — Always use `^` and `$` anchors and be as strict as
  possible. Loosen later if needed.
- **Validate data assumptions before processing** — Do basic input
  validation before expensive operations.
- **One newline around `describe`/`it` blocks** in test files.
- **Test variable names should be descriptive** — e.g.,
  `userWithExpiredSubscriptionAndPendingInvoice` instead of
  `userWithIssue`.
