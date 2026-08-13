---
name: become-another-person
description: Author a self-driving prompt document for another person's Claude Code instance. Use when a task needs someone else's permissions, machine, or environment — pulling data you can't access, running commands under their role, investigating on their host. The document makes their Claude do all the work; the human only reviews an upfront impact disclosure and runs clearly-labeled commands. Don't invoke this for steps your own session can perform.
---

# Become Another Person

A **handoff document** is a markdown file the user sends to a colleague, who
hands it verbatim to their Claude Code instance. Their Claude does the setup,
asks the human to run the few commands that need *their* credentials, then
completes the analysis/deliverable — and cleans up. The human's total effort:
read one disclosure block, run one or two commands, forward the result.

Principles (non-negotiable, bake them into every document):

1. **Never borrow the human's permissions silently.** Their Claude must NEVER
   run privileged commands itself — it writes a script, shows it, and asks the
   human to run it in their own shell (credentials via their own
   `assume`/login, never pasted into the conversation or stored in files).
2. **Impact disclosure before anything runs.** The document instructs their
   Claude to present, as the first interaction, a bulleted disclosure:
   - **Permissions used** — exact role/scopes, read-only vs write
   - **Files/folders created** — exact paths, all inside one workspace folder
   - **Estimated size** — disk (MB) and network transfer, stated separately

   The human may acknowledge as-is, or reply with adjustments/instructions —
   their Claude incorporates them before step 1 begins.
3. **Obvious scripts.** Any script the human runs must be short, commented,
   `set -e`, and readable in one screen — a stranger should see at a glance
   what it does. No curl-pipe-bash, no hidden state, no background jobs.
4. **One workspace folder, cleaned up.** Everything lands in a single named
   folder. The final step tells their Claude to delete intermediates and leave
   only the deliverable(s), and to list exactly what remains.
5. **Wait gates.** After asking the human to run a command, their Claude must
   STOP and wait for confirmation — spelled out in the document, with the ask
   phrased word-for-word ("Please run: `<cmd>` and tell me when it finished").
6. **Data hygiene in deliverables.** State what may not appear in the output
   (credentials, PII, IPs, tokens) and what must (the facts the requester
   needs). Deliverables are self-contained (single-file HTML/md, no external
   resources).

## Process

### 1. Scope the handoff

Establish: the question to answer or artifact to produce; why it needs the
other person (which permission/host); the minimal data to touch (never "pull
everything" when a filter works — stream-and-filter beats download-and-sift);
and the fallback if the first pull comes back empty.

**Done when:** you can fill in every bullet of the impact disclosure from
facts, not guesses — verified paths, measured/estimated sizes, exact role name.

### 2. Author the document

Structure (in this order):

1. **Title + one-paragraph background** with ticket links.
2. **Impact disclosure block** their Claude must show first (pre-written, so
   their Claude can't soften or skip it), ending with: "Reply to acknowledge,
   or tell me what to change."
3. **Step 1 — setup**: their Claude creates the workspace folder and writes
   the script(s), verbatim content included in a fenced block.
4. **Step 2 — the human runs it**: exact ask, word-for-word, including the
   credential command (e.g. `<assume-role-cmd>; bash <script>`). STOP-and-wait
   instruction. Empty-result fallback loop.
5. **Step 3 — analysis + deliverable**: what to compute, hypotheses to weigh
   (with instruction to report what the data actually says, not just confirm),
   deliverable format, privacy rules.
6. **Step 4 — cleanup + return**: delete intermediates, list what remains,
   who to send results to.

### 3. Verify

- Every command in the document is one you have proven exists (correct role
  name, real paths/hosts — verified this session, cite where).
- Dry-read as the recipient: could their Claude execute step 1 with zero
  extra context? Is every wait-gate explicit?
- Size estimate sanity-checked against real listings, not vibes.
