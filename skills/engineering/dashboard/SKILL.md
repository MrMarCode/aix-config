---
name: dashboard
description: Build a single-page HTML dashboard or report that answers a stated list of questions.
argument-hint: "What decision is the dashboard for?"
disable-model-invocation: true
---

A dashboard is a **decision instrument**: one page, built for one decision, carrying what that
decision needs and nothing else. The five steps below get there. Steps 1 and 2 are the whole
interview — keep them short, because every round spent talking is a round not spent building.

## 1. Draft the spine, then hand it to the user

The **spine** is the list of questions the page answers. The user's own questions outrank any
you invent, so your job is to make writing them cheap: profile the data first, arrive with
candidates, let them cut and add.

Profile the source before you ask anything — entities, cardinalities, date range, the obvious
skews, what is missing. Finding facts is your job, never the user's.

Then ask one numbered round and wait. Give every question your recommended answer so "yes to
all" is a valid reply:

```
❓ **Q1** — **Decision**: What will you do differently once you have read this page?
➡️ <your read of it, from the profile>
```

Cover exactly this ground:

1. **Decision** — what act follows from reading it. The title will name this act.
2. **Spine** — the questions it must answer. Offer 6-10 candidates drawn from the profile,
   numbered, and invite replacements. Their edits are the highest-signal input in the run.
3. **Grain** — the unit they act on: channel, service, host, repo, team, region. Top-level
   sections are one per unit at this grain.
4. **Universe** — the complete set the page speaks for, and the total that must **reconcile**.
5. **Exclusions** — what they already know is boring. Ask outright; it is cheaper here than
   as feedback later.
6. **Voice** — pure report, or report plus recommendations.

Mark each spine question **closed** (one number or one ranking settles it) or **open** (they
will slice it a new way every time they look). Open questions earn a query surface; closed
questions earn a stat or a row.

**Grain beats data shape.** Outline the sections at the grain from Q3, not at the shape the
data arrives in — one section per source record is the failure that survives three rounds of
polish, because each round improves a page organised around the wrong thing. Two signals say
the frame is wrong rather than the details: feedback that removes whole sections, and feedback
asking what a heading means. On either, re-derive the outline from the spine before adding
any more data.

## 2. Contract

Write at most fifteen lines and get one approval:

- Title, naming the decision.
- Section list, at the grain.
- Each spine question → the widget that answers it, and where it sits.
- The reconcile identity, as arithmetic.
- Exclusions, listed so they stay out.

Map widgets by question type: closed → a stat tile or a ranked table; open → a filterable
table the user drives; "how did this move" → a time chart with real dates; "how do the parts
reach here" → one diagram.

**The page carries the general view; modals hold the granular.** Every level of detail past
the one the decision needs goes behind a **drill** — click a row, get a modal. A modal is a
full surface, not a tooltip: put the filtered table in it, and the chart too when the
breakdown only makes sense for that one row. This is what keeps the page short while leaving
nothing out, so prefer moving a section into a modal over cutting the data it holds.

That approval is the only gate. After it, build. Questions that surface during the build get
answered in the page and flagged in your summary, not in another interview round.

## 3. Build

Write a generator script that emits one self-contained HTML file, and keep it — feedback
rounds are re-runs of the generator, never hand-edits of the HTML. Open its docstring with
the decision the page serves, so the frame survives contact with later sessions.

Assert the reconcile identity at build time, and print the arithmetic. Shown plus remainder
plus excluded equals total, per section, for every measure the page totals. A page whose
numbers do not account for its universe draws "where is the rest?" on first read.

Trace observed data back to the configuration or source that produced it, and count what you
could not trace. An unattributed row is a row the user cannot act on, and the untraced count
is itself an honest finding.

Libraries, the offline payload, and the drill-down modal: [`LIBRARIES.md`](LIBRARIES.md).

Hold the page to this voice:

- Every section names the question it answers. A section that names none is cut.
- Define each term and unit where it appears. A heading a reader has to ask about has failed.
- Real dates on every axis and label — never week numbers or bare ordinals.
- Every number carries its denominator and its window.
- Totals sit above the table they total, per column.
- Filterable tables and a time chart replace "the five most recent examples"; a handful of
  samples is illustration, and the user asked for analysis.
- The body describes what is; recommendations live in one closing section.
- One file, one document, covering everything — no "part 1 of 2".
- Granularity lives in modals, so the top level of every section stays readable in one screen.

## 4. Click-test before you show it

Open the built file with the browser tools and exercise it, because a broken control reads as
a broken report:

- Console clean of errors.
- Every diagram rendered, not left as source text.
- One drill-down modal opened from a row, showing rows that match it, and closing on ESC.
- A chart inside a modal sized correctly, since a canvas built while hidden has no dimensions.
- One chart hovered, confirming the tooltip names its number, its unit, and its date.
- Icons rendered as glyphs rather than left as empty placeholders.
- Desktop width: content uses the full container.

Screenshot the page and state what you exercised.

## 5. Hand it over for annotation

Print a review link so feedback lands as anchored annotations on the page itself — quote plus
comment beats prose describing a location. Then apply the round through the generator, and
re-run step 4 before showing the result.
