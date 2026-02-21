---
trigger: always_on
---

# Writing & Documentation Rules

## Code Comments

- **Comments explain "why"** — Add comments explaining intent, especially
  for complex chains or non-obvious sorting.
- **Comments belong in code, not MR discussions** — If a decision needs to
  be remembered, put the comment in the code where someone will find it
  years later.
- **Add helpful context to commit descriptions** — When a fix has important
  context, put it in the commit description.
- **Use `https://example.org/`** for test URLs — It's a reserved domain.
- **Add comments explaining "why" for chunking/batching** — If you chunk
  operations, explain why.
- **JSDoc for non-self-documenting methods** — If the method signature isn't
  entirely self-documenting, document it with examples.
- **Comment when order matters** — e.g., "the order is important on these"
  for config arrays.
- **Comment when downstream code modifies upstream objects** — Add a comment
  at the definition site.
- **Keep code comments in sync with code changes**.
- **Show example data formats in templates** — When removing default values,
  show the expected format in a comment.
- **Add code comments pointing to API spec/schema files** — "also update
  the API spec".
- **Update stale references when removing services**.
- **Put context in code comments, not just git blame** — Add a brief "why"
  and a ticket link directly in the code.

## Documentation

- **Define terms before using them** — Create a "Terms Used in This
  Document" section.
- **Use the Oxford comma** — Always.
- **Remove smart quotes** from documentation.
- **Keep tense consistent** — Don't switch between past and present tense
  within the same document.
- **Explain *how we use* important fields** — Don't just describe what a
  field is; explain its significance to our system.
- **Clarify differences between similar fields** — If two fields look alike,
  the documentation must explain how they differ.
- **Use named markdown references** — `[job bookmarks][bookmarks]` not `[1]`
  for maintainability.
- **Explain all schema fields** — Don't leave fields undocumented.
- **Give examples in documentation** — Show what arguments look like.
- **Documentation examples should be realistic** — Include headers and
  cookies, not just bare URLs.
- **Use correct examples in docs** — Users copy-paste from examples, so use
  canonical/correct values.
- **Document recurring maintenance tasks** — Keep a list of recurring tasks
  so they don't get lost.

## Markdown

- **Markdown wraps at 90 characters** — Raw text in markdown files should
  wrap at 90 chars, same as code comments. Code snippets can exceed 90
  chars.
- **One newline before and after code block backticks in markdown**.
