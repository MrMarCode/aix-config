---
description: Code Review
auto_execution_mode: 1
---

# **Code Review Workflow: Current Branch vs Merge-Base with Master**

Perform a structured review of all code changes made on the current branch, using the merge-base with `master` to isolate only the changes introduced on this branch.

---

## **1. Change Summary**
- Determine the merge-base between the current branch and `master`.
- Identify all files changed since the merge-base.
- For each changed file:
  - List the filename and path.
  - Show the specific lines of code added, removed, or modified.
  - Note any newly created or deleted files.

---

## **2. Security Review**
- Analyze the changes for potential security vulnerabilities:
  - Input validation and sanitization
  - Authentication and authorization logic
  - Sensitive data handling
  - Use of external libraries or APIs
- Phrase feedback as questions unless a vulnerability is clearly present:
  - “Is this input properly validated before use?”
  - “Could this expose sensitive data under certain conditions?”

---

## **3. Similarity Scan**
- Search the entire codebase for similar logic, patterns, or functions.
- Identify:
  - Where similar functionality exists
  - How it is implemented elsewhere
  - Whether the new implementation aligns with existing standards

---

## **4. Standards & Best Practices Comparison**
- Compare the new code to similar existing code.
- Evaluate consistency with:
  - Project conventions and naming patterns
  - Error handling strategies
  - Modularity and readability
- Ask questions like:
  - “Should this follow the same pattern as in `services/auth.js`?”
  - “Is this naming consistent with our convention in `components/`?”

---

## **5. Feedback & Questions**
- Phrase most comments as questions unless something is clearly incorrect.
- Highlight areas for improvement or clarification.
- Use a constructive tone to guide the developer toward better practices.
- IMPORTANT: Do not compliment developer needlessly, positive validation is not important.

---

## **Output Format**
- Present findings as one bulleted or numbered list of questions.
- IMPORTANT: each point MUST be concise.
- Include inline code snippets where helpful.
- Clearly separate:
  - Observations
  - Questions
  - Confirmed issues