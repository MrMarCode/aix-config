---
trigger: always_on
---

# Naming Conventions

## Classes

   * **PascalCase** nouns (e.g., `UserAccount`)
   * Singular form, match table names when applicable

## Functions

   * **Static functions**: snake_case (e.g., `get_user_data`)
   * **Instance functions**: camelCase (e.g., `getUserData`)
   * **Private/protected**: camelCase with underscore prefix (e.g., `_privateMethod`)
   * Name describes complete purpose:
      * Return single value: `get` + column name
      * Return multiple rows: `list` + table name
      * No return: strong verb + noun
      * Boolean: start with "is" (e.g., `isPublished`)

## Variables

   * **Static variables**: snake_case
   * **Constants**: UPPER_SNAKE_CASE
   * **Instance/scoped variables**: camelCase
   * **Private/protected**: camelCase with underscore prefix
   * **Arrays**: plural form (except associative arrays)
   * **Booleans**: imply true/false naturally
   * 4-20 characters optimal, specific purpose

## Files

   * **Classes**: PascalCase matching class name (e.g., `User.js`)
   * **Functions/objects**: kebab-case (e.g., `my-function.js`)
   * **Tests**: `ClassTheyAreTesting.test.js`

## Abbreviations & Acronyms

   * Use sparingly, prioritize readability
   * Be consistent across codebase
   * Acronyms: ALL_CAPS except when first letter of camelCase property
   * Remove non-leading vowels for abbreviations
   * Must be pronounceable

## General Naming Principles

   * UPPER_SNAKE_CASE for constants — Don't add values to constants at
     runtime.
   * Enums use UpperCamelCase.
   * Naming accuracy matters — Variable/function names should precisely
     describe what they represent.
   * Avoid acronyms mid-variable-name — `_getSubtitlesURL` is better
     than `_getVTTURLFromMediaItem`.
   * Function names must match what they do — `_getByDate` is misleading
     if it only looks up videos. Use `_getVideoByDate` instead.
   * Abbreviation casing must be consistent across the codebase.
   * Use existing constants — Don't hardcode values that already exist as
     constants elsewhere.
   * Naming should not be client-specific — `paginationTotal` is better
     than `displayTotal`.
   * Rename `opts` to `overrides` when the parameter provides override
     values for defaults.
   * Function names should describe what they return —
     `get_error_code_from_yaml` is clearer than `get_error_code`.
   * Config key names should be descriptive —
     `product-to-detail-page-id` is better than a vague abbreviation.
   * Service names should describe what they do —
     `os-events-distributor` not `os-event-logger`.
   * Be consistent with plurals — If existing services use
     `os-events` (plural), new related services should too.
   * Column names should describe what the data is, not its type —
     `event_datetime` not `timestamp_column`.
   * Be precise with language identifiers — "locale code" vs "internal
     language code" vs "locale" are different things.
   * Be explicit about CLI parameter names — Use `--language-codes` not
     `--languages` to avoid ambiguity with "locale".
   * Don't prefix types with the wrong system name — If an enum comes
     from SystemA, don't call it `SystemBType`.
   * Name event categories precisely — `data-event` over `data-anomaly`
     (not all events are anomalies); avoid overloaded terms like
     "production" in event names.

## Case Definitions

   * **PascalCase**
   * **camelCase**
   * **kebab-case**
   * **snake_case**
   * **UPPER_SNAKE_CASE**
