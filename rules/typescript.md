---
trigger: glob
globs: "**/*.ts,**/*.js"
---

# TypeScript Coding Standards

## **CRITICAL: const Declarations**
   * **ALWAYS** use `const` by default; use `let` only when mutation is unavoidable
   * Group consecutive single-line declarations with commas
   * Multi-line declarations stand alone (only one per block)
   ```typescript
   const firstVar = '',
         secondVar = '';

   const multilineVar = {
      key: value,
      key2: value2,
   };
   ```

## Functions & Arrow Functions
   * **ALWAYS** use block body for arrow functions and function expressions: `() => { return x; }` instead of `() => x`
   * **ALWAYS** write functions with a block body over concise body
   * Use rest parameters instead of `arguments`
   * Parentheses around parameters, space before/after arrow
   * Define methods as class methods

## Immutability & Functional Style
   * Return new values instead of mutating inputs
   * Use `.map()`, `.filter()`, `.reduce()`, `.find()` over `for` loops
   * Use spread/concat/slice for array operations
   * Pure functions: same input = same output

## Async
   * Prefer `async/await` over Promise chaining
   * Use `Promise.all()` for concurrent operations
   * Never use `console.log` — default to `console.info`

## Destructuring
   * ✅ Basic object/array, array with rest, renaming
   * Use explicit property access instead of object rest: `const { a } = obj; const rest = { b: obj.b };`
   * Use intermediate variables instead of deep destructuring

## Types
   * Explicit types for all variables, exports, and return values
   * Use primitives: `string`, `number`, `boolean`
   * Spacing: `varName: Type` (no space before colon, one space after)
   * Avoid `any` — use `unknown` or specific types. "`any` spreads like
     a disease." Prefer `unknown` or `StringUnknownMap` over `any`.
   * No blind type casts — Casting loses type safety. If you need to
     cast, the types are wrong.
   * Use `[k in EnumType]` mapped types to ensure exhaustive coverage of
     enum values in lookup tables.
   * Only use `async` where you use `await` — Don't mark functions
     `async` unnecessarily.
   * Define proper interfaces for function parameters — Don't accept
     `AttributeMap` or `any` when you know the shape of the data.
   * Use `isEnumValue` for validation — e.g.,
     `isEnumValue(Prefer, rawPrefer) ? rawPrefer : Prefer.ContentLoose`.
   * Use utility types — e.g.,
     `RequireOptional<FinderOptions, 'lank'>` to make optional fields
     required in specific contexts.
   * Use type guards to eliminate type assertions.
   * Create specific types for filtered data — When filtering `_source`
     fields from ES, create a type that only defines the fields actually
     returned.
   * Rename awkward SDK types on import — When the SDK exports `_Object`,
     alias it: `import { _Object as S3Object }`.
   * Use `StrictUnion` for discriminated union types — Prevents TypeScript
     from allowing properties from one variant on another.
   * Use Zod for runtime validation of external data — When parsing JSON
     from external sources, use Zod schemas.
   * Define Zod types as `ZTypeName`.
   * Define real types for data you own — Create proper TypeScript
     interfaces rather than using `any[]` or `object[]`.
   * Make generic utility functions return values —
     `processZipFileFromPath<T>` should let the processor return a value
     to the caller.
   * Avoid underscore in TypeScript — The types are poorly-typed. Use
     native functions like `.includes()`, `.filter()`,
     `Object.keys().forEach()`, or toolbox utilities instead.

## Error Handling
   * No space between `catch` and parentheses: `catch(error) {`

## Function Signatures & Style
   * Function signatures on one line — Multi-line signatures are
     distracting. Keep them single-line even if it means ignoring max-len
     on that line.
   * Use JSDoc comments so intellisense picks them up, not regular
     comments.
   * Add JSDoc to exported interfaces — At minimum a one-sentence summary
     explaining why this interface exists and how it relates to others.
