---
description: Queue multiple category requests and run them as one batch
agent: sfx-writer
---

Run a multi-category batch generation for the SFX Studio library.

**Batch request:** $ARGUMENTS

## Parse

Parse the request into category/quantity pairs. The user may phrase it naturally:
- "3 stingers, 2 ambience, 5 news"
- "stinger:3 bed:2 transition:4"

Valid categories: `ambience`, `stinger`, `transition`, `bed`, `foley`, `jingle`, `news`, `misc`.

- If `$ARGUMENTS` is empty, ask the user what they want in the batch and stop.
- Ignore/flag any unrecognized category and confirm the parsed plan (category → quantity) before generating, so a typo never silently produces the wrong batch.

## Run the batch

1. **Read context once.** Load `docs/product-foundation.md`, `docs/sfx-standard-context.md`, and `AGENTS.md` if present. Read `logs/generation_log.json` once up front and reason over the full library across all requested categories. If the log is missing, create it as `[]` and note the fresh start.
2. **Seed angles across the whole batch.** Process each category in turn, but enforce distinctness **globally**: no slot may share more than one major characteristic with another slot in this batch *or* with an existing library entry. Track angles already claimed earlier in the batch so later slots diverge.
3. **Council every prompt.** For each prompt run the full council (@sfx-ear, @sfx-director, @sfx-librarian), apply council rules (below-6 triggers a revision addressing that critic; max 2 rounds), and decide. You hold final authority.
4. **Generate, throttled.** Generate approved prompts via `scripts/generate.py`. **Throttle the entire batch to the account concurrency limit** — do not fire all requests at once. Serialize to the tier cap (Free 2, Starter 3, Creator 5, Pro 10; assume Free = 2 if unknown and say so).
5. **Organize and log.** Route and name each file with `scripts/organizer.py` per the naming convention, then append one complete schema entry per generation to `logs/generation_log.json`.

If `scripts/generate.py` or `scripts/organizer.py` is not yet authored, output the approved prompts, params, and intended log entries in the TUI and tell the user, rather than failing silently.

## Report

Finish with a final summary: how many SFX were generated per category, how many needed revisions, any prompts flagged for manual review, and the total estimated character cost (100 per auto-duration generation, `25 × duration_seconds` for fixed).
