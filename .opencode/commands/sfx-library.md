---
description: Browse the current SFX pool by category
agent: sfx-writer
---

Show the current state of the SFX Studio library. **This is read-only — do not generate, rename, move, or delete anything.**

Here is the on-disk library tree:

!`find sfx_library -type f -name "*.mp3" 2>/dev/null | sort`

Here is the generation log:

@logs/generation_log.json

## Present a clear, browseable summary

Cross-reference the on-disk files against the log (each log entry's `output_path`/`output_filename` should map to a real file; flag mismatches).

1. **Per-category counts** — how many SFX exist in each category folder: `ambience`, `stinger`, `transition`, `bed`, `foley`, `jingle`, `news`, `misc`. Show a small table.
2. **Per-category listing** — for each non-empty category, list its files with a one-line description drawn from the `prompt` and `sonic_angles` in the log. Where a file exists on disk but has no log entry (or vice versa), call it out explicitly.
3. **Coverage notes** — flag categories that are empty or thin (fewer than 3 entries), and point out where the pool is saturated or lacks sonic variety (many entries sharing instrumentation/attack/texture). Reference the broadcast roles in `docs/sfx-standard-context.md` to suggest which gaps matter most for a working library.
4. **Next-step suggestion** — based on the gaps, suggest concrete `/sfx-generate` or `/sfx-batch` calls to balance the pool.

## Edge cases

- If `logs/generation_log.json` is empty, missing, or an empty array, say the library is empty and suggest running `/sfx-generate [category] [qty]` to start.
- If the log has entries but no files are on disk (or no files but the log is populated), report the inconsistency plainly so the user can investigate before generating more.
