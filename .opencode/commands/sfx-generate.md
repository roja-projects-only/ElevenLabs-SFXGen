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

1. **Read context.** Load `docs/product-foundation.md`, `docs/sfx-standard-context.md`, and `AGENTS.md` if present. Then read `logs/generation_log.json` and reason over every existing entry in the **$1** category to understand what already exists. If the log is missing, create it as `[]` and note the library is starting fresh.
2. **Seed angles.** Assign **$2** distinct sonic fingerprints (instrumentation, attack, texture, spatial feel, frequency emphasis). No two slots may share more than one major characteristic, and none may closely resemble an existing library entry. Push toward sonic territory the log shows is thin.
3. **Write prompts.** Produce **$2** ElevenLabs-optimized prompts following the prompting rules and the **Per-Category Generation Spec** for **$1** (1,000-char cap, audio terminology, explicit sequences, BPM/key for musical elements, correct `prompt_influence`, `loop`/`duration_seconds`, `output_format: mp3_44100_128`).
4. **Convene the council.** For each prompt, delegate to @sfx-ear, @sfx-director, and @sfx-librarian for independent 1–10 scores, passing the category for context.
5. **Resolve.** Any score below 6 triggers a revision round addressing that critic's rationale; max 2 rounds per prompt. You hold final decision authority — force approval or flag for manual review after the cap.
6. **Generate.** For each approved prompt, call `scripts/generate.py` with its flags: `--text`, `--category` (**$1**), `--prompt-influence`, `--duration` (omit for auto), `--loop` (for beds/ambience), `--output-format` (default `mp3_44100_128`), `--tier` (assume `free` = 2 concurrent if unknown, and say so), and `--out` (a temp path). The CLI throttles to the tier via an in-process semaphore — do not run multiple generate processes in parallel for one batch.
7. **Organize and log.** Call `scripts/organizer.py --src <out> --category $1 --descriptor <sonic> --mood <mood>`; it prints JSON `{filename, id, output_path}` — use `id` as the log entry `id`. Then append one complete entry per generation to `logs/generation_log.json` using the full log schema (the `scripts/sfx_studio/` package exposes `log.build_entry()` / `log.append_entry()` if you prefer a single Python call over hand-editing the JSON).

Show the council debate and your final decisions in the TUI as you go. Finish with a short summary: how many were generated, how many needed revisions, and any flagged for manual review.
