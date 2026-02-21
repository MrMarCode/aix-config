---
trigger: always_on
---

# Comments & Documentation

## Function Documentation

Required JSDoc format:

```javascript
/**
 * Description of function purpose
 *
 * @param Type $param - description (optional, default value)
 * @return Type - description of return value
 */
```

## Comments

   * Only add a comment if:
      * The code's rationale is not obvious from naming/context, or the implementation is nonstandard.
      * The comment answers "why," **not** "what" or "how."
      * The surrounding code uses comments in a similar way.
      * Do not comment on types, parameters, or usage that are clear from code or naming.
      * When in doubt, omit the comment.
   * See examples:
      * Allowed: // Must support legacy clients that send this header, e.g:...
      * Not allowed: // The IAM role to use for the Lambda function. Must be provided by the caller.
