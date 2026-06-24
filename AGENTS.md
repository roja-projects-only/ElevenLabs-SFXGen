# SFX Studio — Repo-Level Brain

## Project Context

A personal sound-effects generation workspace for radio broadcast production. Powered by an **OpenCode** harness (TUI + multi-agent runtime), **DeepSeek V4 Flash** as the writer and critic model, and **ElevenLabs Sound Effects API** for audio rendering. An agent council of four roles handles the creative pipeline: `sfx-writer` orchestrates, three critics (`sfx-ear`, `sfx-director`, `sfx-librarian`) evaluate each prompt. Uniqueness is enforced via agent-based reasoning over `logs/generation_log.json` — no embedding models or external similarity tools. The user directs via commands; the council does the creative work.

## Stack

| Layer | Tool |
|---|---|
| Harness & TUI | OpenCode |
| Writer + Council | `deepseek/deepseek-v4-flash` (writer + critics) |
| Audio Generation | ElevenLabs Sound Effects API |
| Uniqueness | Agent-based (sfx-writer + sfx-librarian via `generation_log.json`) |
| Prompt Memory | `logs/generation_log.json` |

## Folder Map

```
AGENTS.md                        # This file — repo-level brain
opencode.json                    # OpenCode config (model, default agent)
.gitignore                       # Git ignore rules
.ignore                          # OpenCode index overrides
.env.example                     # Env var template

.opencode/
├── agents/
│   ├── sfx-writer.md            # Primary orchestrator
│   ├── sfx-ear.md               # Sonic coherence critic
│   ├── sfx-director.md          # Broadcast utility critic
│   └── sfx-librarian.md         # Uniqueness critic
└── commands/
    ├── sfx-generate.md          # /sfx-generate [category] [qty]
    ├── sfx-batch.md             # /sfx-batch
    └── sfx-library.md           # /sfx-library

scripts/
├── generate.py                  # ElevenLabs API call + download
├── organizer.py                 # Auto-naming + folder routing
└── sfx_studio/                  # Package (other lane)

sfx_library/
├── ambience/
├── stingers/
├── transitions/
├── beds/
├── foley/
├── jingles/
├── news/
└── misc/

logs/
└── generation_log.json          # Prompt history — append-only, never delete

docs/
├── product-foundation.md        # Full canonical spec
└── sfx-standard-context.md      # Broadcast SFX standards + reference table
```

## Agent Roles

| Agent | Role | Authority |
|---|---|---|
| **sfx-writer** | Primary orchestrator — reads history, seeds sonic angles, writes prompts, convenes council, calls scripts | Final decision authority |
| **sfx-ear** | Sonic coherence critic — is the sound physically achievable and acoustically specific? | Score 1–10, advisory |
| **sfx-director** | Broadcast utility critic — does the SFX serve real radio production? | Score 1–10, advisory |
| **sfx-librarian** | Uniqueness critic — is the prompt too similar to any existing library entry? | Score 1–10, advisory |

## Council Rules

1. All three critics score each prompt **independently**, 1–10.
2. Any score **below 6** triggers a revision round addressing that critic's rationale.
3. **Maximum 2 revision rounds per prompt** — hard cap to control token cost.
4. After the cap, `sfx-writer` either **force-approves** or **flags for manual review**.
5. Council debate is visible in the OpenCode TUI.
6. All scores + notes (including from earlier rounds) are always appended to `generation_log.json`.

## Uniqueness System

**Layer 1 — Sonic angle seeding (pre-generation).** Before writing prompts for a batch, `sfx-writer` reads `generation_log.json` and assigns each slot a distinct sonic fingerprint across instrumentation, attack, texture, spatial feel, and frequency emphasis. No two slots in the same batch share more than one major characteristic.

**Layer 2 — sfx-librarian council vote (post-generation).** `sfx-librarian` independently cross-references each new prompt against the full log history. A score below 6 on uniqueness sends the prompt back for divergence.

## Naming Convention

Files are auto-named by `organizer.py` using the format:

```
[category]_[sonic_descriptor]_[mood]_[index].mp3
```

**Index** is zero-padded 3-digit, scoped per category folder. **Log entry `id`** = filename without extension. Files route to `sfx_library/<category>/`.

### Category → Folder Mapping

| Category | Folder | Plural? |
|---|---|---|
| ambience | `sfx_library/ambience/` | same |
| stinger | `sfx_library/stingers/` | stingers |
| transition | `sfx_library/transitions/` | transitions |
| bed | `sfx_library/beds/` | beds |
| foley | `sfx_library/foley/` | same |
| jingle | `sfx_library/jingles/` | jingles |
| news | `sfx_library/news/` | same |
| misc | `sfx_library/misc/` | same |

**Examples:** `stinger_brass_punchy_001.mp3`, `ambience_rain_interior_002.mp3`, `news_electronic_rising_003.mp3`.

## Log Integrity

`logs/generation_log.json` is a JSON **array**, **append-only**. NEVER delete or reorder entries — `sfx-librarian` depends on the full history for uniqueness reasoning. If missing, create as `[]`.

## Categories

`ambience`, `stinger`, `transition`, `bed`, `foley`, `jingle`, `news`, `misc`

## Commands

| Command | Description |
|---|---|
| `/sfx-generate [category] [qty]` | Generate N SFX of a given category |
| `/sfx-batch` | Queue multiple category requests and run as one batch |
| `/sfx-library` | Browse the current SFX pool by category |

## Environment

`ELEVENLABS_API_KEY` goes in `.env` at repo root. Never commit to Git. Use the `setup-api-key` skill to configure safely — never paste keys into chat.

## Pointers

- **Full spec:** `docs/product-foundation.md`
- **Broadcast SFX standards:** `docs/sfx-standard-context.md`
- **ElevenLabs SDK how-to:** `.agents/skills/sound-effects/SKILL.md`
