---
name: git
description:
  Use before committing ANYTHING to ensure proper commit message and branch naming.
---

## Git

### Commit Messages

   * Start with type followed by a colon and a space
   * Types include:
      * build: Changes that affect the build system or external dependencies
      * chore: Other changes that don't modify src or test files. Also used for releases
      * ci: Changes to our CI configuration files and scripts
      * config: Changes to how a service runs
      * docs: Changes only affecting documentation
      * feat: A new feature
      * fix: A bug fix
      * perf: A code change that improves performance
      * refactor: A code change that neither fixes a bug nor adds a feature
      * revert: Reverts a previous commit
      * style: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc.)
      * sub(type): Any smaller chunk of a **defined** type. eg: sub(feat): A smaller feature
      * test: Adding missing tests or correcting existing tests
   * Include (#xxxxx) (where xxxxx is the issue number) in the subject of all commit
   messages as the last item.
   * The header (type + subject + issue #) must be no more than 72 characters long
   * The max line length of the body is 90 characters
   * Use markdown formatting in your commit messages, including a space before either an asterisk or a numbered list if doing ordered/unordered lists
   * Commit messages should focus more on explaining the "why" than the how

### Branch Names

   * Use kebab-case
