---
trigger: always_on
---

# Terminal & Command Rules

## Command Batching

- **Chunk successive commands into a single terminal call** — Group
  commands you plan to run in succession into one human-readable call
  for easy review. Separate with `&&` or newlines, not separate
  invocations.

## Temp Files

- **Use a `tmp/` folder accessible via run-box, not `/tmp`** — When
  generating temp files, create a `tmp` directory within the project
  or a run-box-accessible location. This allows run-box to examine
  output directly. Avoid `/tmp` for file access reasons. Delete items
  in the `tmp` folder when done.

## Command Estimation

- **Estimate terminal command count before executing** — If you
  suspect you will need to run several terminal commands (outside
  run-box) in a row, guesstimate how many and write it out before
  executing. Example: `cmd 1~6: read output from aws stack`. If the
  user skips, assume they want commands grouped more or try another
  method. If they keep skipping, ask using the question ask tool.

## Testing Unknown Commands

- **Look up unknown commands or libraries first** — If unsure how a
  command or library works, look it up, then create a simple
  environment to test it using run-box.
