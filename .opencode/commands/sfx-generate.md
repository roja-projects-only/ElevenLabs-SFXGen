---
description: Generate N sound effects of a given category
agent: sfx-writer
---

Generate sound effects for the SFX Studio library.

**Category:** $1
**Quantity:** $2

## Preconditions

- Valid categories: `ambience`, `stinger`, `transition`, `bed`, `foley`, `jingle`, `news`, `misc`.
- If **$1** is empty or not one of the valid categories, ask which category to generate and stop.
- If **$2** is empty, default to **1**. If **$2** is not a positive integer, ask for a valid quantity and stop.

## Run the full generation pipeline as defined in your orchestrator instructions

1. **Read context (targeted).** Load `AGENTS.md` (primary reference; fall back to `docs/product-foundation.md` only if it lacks a needed detail). Read `logs/generation_log.json` and reason over existing entries in the **$1** category. Grep `docs/sfx-standard-context.md` for the **$1** keyword and read only the matching section — do NOT load the full reference table. If the log is missing, create it as `[]` and note the library is starting fresh. Do NOT read script source files or the sound-effects skill unless debugging.
2. **Seed angles.** Assign **$2** distinct sonic fingerprints (instrumentation, attack, texture, spatial feel, frequency emphasis). No two slots may share more than one major characteristic, and none may closely resemble an existing library entry. Push toward sonic territory the log shows is thin.
3. **Write prompts.** Produce **$2** ElevenLabs-optimized prompts following the prompting rules and the **Per-Category Generation Spec** for **$1** (1,000-char cap, audio terminology, explicit sequences, BPM/key for musical elements, correct `prompt_influence`, `loop`/`duration_seconds`, `output_format: mp3_44100_128`).
4. **Pre-submission checklist.** Before dispatching the council, verify each prompt against the Per-Category Generation Spec: duration matches category spec, envelope/texture fits the category role, `prompt_influence`/`loop`/`duration_seconds` match defaults, prompt is within 1,000 characters. Fix failures locally — do not spend council tokens on prompts that violate known constraints.
5. **Convene the council.** Use the **Council Dispatch Strategy** from your orchestrator instructions: per-prompt calls for N≤3, single batch call per critic for N=4–10, sub-batches of 8–10 for N>10. Each critic's system prompt already defines its role — do NOT re-inject role descriptions. Include "Score each prompt independently" in every batch call. The librarian reads `logs/generation_log.json` itself and filters to same-category entries.
6. **Resolve.** Any score below 6 triggers a revision round addressing that critic's rationale; max 2 rounds per prompt. You hold final decision authority — force approval or flag for manual review after the cap.
7. **Generate.** Write a batch JSON file with all approved prompts and call `scripts/generate_batch.py --input <batch.json> --tier <tier>` to generate, name, and route all files in one call. The script handles tier concurrency internally. Assume `free` tier (2 concurrent) if unknown — surface this assumption in the TUI. For N=1, you may use `scripts/generate.py` directly.
8. **Log.** Use the batch script's output (filenames, IDs, paths) to append one complete entry per successful generation to `logs/generation_log.json` via `log.build_entry()` + `log.append_entry()` from the `scripts/sfx_studio/` package. For failed items, decide whether to retry or skip.

Show the council debate and your final decisions in the TUI as you go. Finish with a short summary: how many were generated, how many needed revisions, and any flagged for manual review.
