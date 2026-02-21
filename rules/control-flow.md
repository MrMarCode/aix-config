---
trigger: always_on
---

# Control Flow & Variables

## Control Structures

   * Most common case in `if` (not `else`)
   * Use blocked scope in switch statements
   * Use positive logic over negative
   * Check error conditions early with early returns
   * Ternary operator only for simple conditions

## Variable Best Practices

   * Declare in lowest possible scope, close to first use
   * Declare at top of scope before statements
   * Initialized variables before uninitialized
   * Avoid modifying input parameters (except immediate sanitization)
   * Avoid global variables (constants only)
   * Always sanitize user input
