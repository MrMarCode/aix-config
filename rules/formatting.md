---
trigger: always_on
---

# Formatting Rules

## Indentation

   * **3 spaces**
   * Wrapped lines: indent one level from first line
   * Chained functions: indent one level from chain start
   * Empty lines contain zero characters

## Braces & Structure

   * Always use braces for conditionals/loops (even single line)
   * One blank line between unrelated statements
   * One-two blank lines between functions

## Spacing & Operators

   * Function calls: `myFunction()`
   * Empty arrays/objects: no spaces (`[]`, `{}`)
   * Multi-line arrays/objects: always trailing comma `{
     'one': 1,
     }`

## Parentheses

   * Use for clarity even when not required
   * Nested parentheses touch: `((x))`

## Line Length

   * Code must be 140 characters or less
   * Comments must be 91 characters or less
   * Lengthy comments should be split into multiple lines (`// ...reached 91 or less\n// ...)

## Whitespace & Misc

   * Trailing newlines required — Files must end with exactly one trailing
     newline.
   * Extra blank lines flagged — Reviewers consistently flag extra blank
     lines.
   * One blank newline after the final function in a class.
   * Don't quote object keys unless absolutely needed.
   * Don't reorder/reformat code unnecessarily — It creates noise in code
     reviews.
