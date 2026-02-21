---
description: test-driven-development
auto_execution_mode: 1
---

1. Write what you need to accomplish in a comment. 
2. Write proposed API's to use.
3. Create a small and simple test environment to validate the API works like that. 
4. Run that script to test it. 
5. Write down what you learned in a markdown file called "packagename-api.md"
6. Stub out the actual production code that will use these API's to accomplish the goal.
7. Re-read the packagename-api.md and fill in the stubbed out functions using the API.
8. Finish with automated tests. 
9. Run the tests.
10. Write the documentation for how it is to be used.
11. Delete verbose comments. Replace important comments with short explanations (ONLY answer WHY not what or how)

IMPORTANT: functional programming is best. It's easier to test and type. Use typed objects to describe. Use zod schemas where validation of the data is important. avoid using any. avoid for loops, use .map and .filter and reduce, etc... Prefer async await instead of promise.catch.then, etc...