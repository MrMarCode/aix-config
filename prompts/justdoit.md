---
description: Create a plan, write the plan to markdown file(s), create Beads using the br CLI, implement the beads, and don't stop until all Beads are closed.

auto_execution_mode: 1
---

First create a plan using the `/to-spec` skill. If it is a large change, break the
plan into multiple documents.

If it is a very large change, it is acceptable for sub-plans to be a plan to _create_
a plan. Sub-plans should follow the same spec format specified in the `/to-spec` skill.

Writing the plan should involve online research using the latest relevant documentation
and sources.

Write these plan files to markdown documents.

Then, translate the plan(s) into Beads using the `br` CLI tool (see
`/setup-matt-pocock-skills` for tracker setup). Use `/to-tickets` to break the spec
into tracer-bullet tickets with blocking edges. Include enough detail for each Bead
so that subagents can implement without confusion, and include references back to
the original plan md files as needed for more context.

For each major piece, include a verification step that involves running
linting/type-checking/tests _and_ manual QA testing for affected components/code,
and a code review using the `/code-review` skill. Address all bugs and concerns.

Address concerns immediately and do not mark them as out of scope. It is always in-scope.
Working, production-ready code with no TODOs or stubs or half-baked solutions are ALWAYS
the priority.

Once all Beads are created, list them all in another markdown document.

Finally, ensure there is a Bead for a final verification that follows this process:

For every Bead listed in the markdown document, have an agent review what work was done.
The agent should prove whether or not the requirements for the Bead were fully implemented
and that it was not skipped, stubbed, or half-baked. "Proof" means an explanation and
links to specific code files and lines of code. For large features, that would include
MULTIPLE confirming pieces of evidence and links.

If the agent finds implementation is incomplete, address it immediately and then have the
agent re-review and pick up the review process where it left off.

Finally, another agent should review the proof document as to whether the proof was
sufficient.

DO NOT SKIP THIS STEP.

Continue and don't stop until all Beads are closed and all proof is finalized and
reviewed.