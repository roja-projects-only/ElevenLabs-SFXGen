# SFX Studio — Product Foundation

## What This Is

A personal SFX generation workspace for radio broadcast production. You give a command, the agent council does the creative work, ElevenLabs generates the audio, and files land organized in your library. No manual prompting. You are the director.

---

## Stack

| Layer | Tool |
|---|---|
| Harness & TUI | OpenCode |
| Writer + Council | DeepSeek V4 Flash (configured in OpenCode) |
| Audio Generation | ElevenLabs Sound Effects API |
| Uniqueness Check | Agent-based (sfx-writer + sfx-librarian via generation_log.json) |
| Prompt Memory | `logs/generation_log.json` |

---

## Repo Structure

```
sfx_studio/
├── AGENTS.md                        # Repo-level brain — project context, council rules,
│                                    # naming conventions, revision cap, folder map
├── opencode.json                    # Agent definitions, model assignments, permissions
│
├── .opencode/
│   ├── agents/
│   │   ├── sfx-writer.md            # Primary agent — orchestrates full generation pipeline
│   │   ├── sfx-ear.md               # Subagent — sonic coherence critic
│   │   ├── sfx-director.md          # Subagent — broadcast utility critic
│   │   └── sfx-librarian.md         # Subagent — uniqueness critic (cross-refs log)
│   └── commands/
│       ├── sfx-generate.md          # /sfx-generate [category] [qty]
│       ├── sfx-batch.md             # /sfx-batch
│       └── sfx-library.md           # /sfx-library
│
├── scripts/
│   ├── generate.py                  # Calls ElevenLabs API, handles download
│   └── organizer.py                 # Auto-naming + folder routing
│
├── sfx_library/
│   ├── ambience/
│   ├── stingers/
│   ├── transitions/
│   ├── background_music/
│   ├── foley/
│   ├── jingles/
│   ├── news/
│   └── misc/
│
└── logs/
    └── generation_log.json          # Prompt history for cross-session uniqueness memory
```

---

## Agent Roles

### `sfx-writer` — Primary
Orchestrates the full pipeline. Reads `AGENTS.md` and `generation_log.json` before writing any prompt. Reasons over prompt history to seed unique sonic angles per batch slot, writes ElevenLabs-optimized prompts, delegates to the council, incorporates feedback, and calls the scripts. Has final decision authority — approves, rejects, or flags for manual review after max revision rounds.

### `sfx-ear` — Subagent (Critic)
Evaluates sonic coherence. Scores the prompt 1–10 and flags whether the described sound is physically achievable and acoustically specific enough for ElevenLabs to render correctly.

### `sfx-director` — Subagent (Critic)
Evaluates broadcast utility. Scores 1–10 and flags whether the SFX serves actual radio production — right energy, right duration, right function for the category.

### `sfx-librarian` — Subagent (Critic)
Evaluates uniqueness. Reasons over `generation_log.json` and flags whether the prompt is semantically too similar to any existing library entry. Primary uniqueness gate in the council.

---

## Council Rules (defined in `AGENTS.md`)

- All three critics score each prompt independently (1–10)
- Any score below **6** triggers a revision round
- Maximum **2 revision rounds** per prompt — after that, `sfx-writer` forces approval or flags for manual review
- Council debate is visible in the OpenCode TUI
- Council results and final prompts are always appended to `generation_log.json`

---

## Uniqueness System

Two-layer agent-based approach — no external scripts or embedding models required.

**Layer 1 — Sonic angle seeding (pre-generation)**
Before writing prompts for a batch, `sfx-writer` reads `generation_log.json` and reasons over the full prompt history. It assigns each batch slot a distinct sonic fingerprint — different instrumentation, attack, texture, spatial feel, frequency emphasis. No two slots in the same batch share more than one major characteristic.

**Layer 2 — sfx-librarian council vote (post-generation)**
`sfx-librarian` independently cross-references each new prompt against `generation_log.json` as part of the council debate. It reasons semantically — not by threshold — over whether the proposed SFX would be too similar to anything already in the pool. A score below 6 on uniqueness grounds sends the prompt back to `sfx-writer` for divergence.

---

## ElevenLabs API Reference (from research brief)

**Endpoint:** `POST https://api.elevenlabs.io/v1/sound-generation`
**Auth:** `xi-api-key` header

| Parameter | Default | Constraints |
|---|---|---|
| `text` | — | Required. Max **1,000 characters** |
| `model_id` | `eleven_text_to_sound_v2` | — |
| `duration_seconds` | `null` (auto) | 0.5–30 seconds; auto is cheaper |
| `prompt_influence` | `0.3` | 0–1; raise to 0.7–0.9 for tight specs |
| `loop` | `false` | MP3 only; use for background_music and ambience |
| `output_format` | — | Query param; default `mp3_44100_128` |

**Recommended output format:** `mp3_44100_128` for broadcast. Looping requires MP3 — PCM not available for loop mode.

**Cost:** Auto duration = 100 characters flat per generation. Fixed duration = 25 characters per second. Always prefer auto unless duration is a hard requirement.

**Concurrency limits by tier:**

| Tier | Concurrent Requests |
|---|---|
| Free | 2 |
| Starter | 3 |
| Creator | 5 |
| Pro | 10 |

Throttle `/sfx-batch` with `asyncio.Semaphore(N)` in `generate.py` where N = your tier limit.

**Prompting rules for sfx-writer:**
- Hard cap: 1,000 characters per prompt
- Use audio production terminology: `braam`, `whoosh`, `drone`, `glitch`, `impact`, `one-shot`
- Describe sequences explicitly: `"Sound A, then Sound B"`
- Include BPM and key for musical elements
- Set `prompt_influence: 0.3` for creative/atmospheric; raise to `0.7–0.9` for tightly specified stingers
- Set `loop: true` + 30 seconds for background_music and ambience

---

## generation_log.json Schema (from research brief)

Each entry in `logs/generation_log.json` follows this structure:

```json
{
  "id": "stinger_brass_punchy_001",
  "prompt": "Punchy brass stab with tight reverb tail, one-shot, F minor, 2 seconds",
  "category": "stinger",
  "sonic_angles": {
    "instrumentation": "brass",
    "attack": "punchy",
    "texture": "tight",
    "spatial": "dry with short reverb",
    "frequency": "mid-high"
  },
  "duration_seconds": null,
  "prompt_influence": 0.7,
  "output_filename": "stinger_brass_punchy_001.mp3",
  "output_path": "sfx_library/stingers/stinger_brass_punchy_001.mp3",
  "council_scores": {
    "sfx-ear": 8,
    "sfx-director": 9,
    "sfx-librarian": 9
  },
  "council_notes": {
    "sfx-ear": "Acoustically coherent, achievable",
    "sfx-director": "Serves broadcast stinger function well",
    "sfx-librarian": "No similar entry in library"
  },
  "revision_count": 0,
  "timestamp": "2026-06-24T10:00:00Z",
  "model_id": "eleven_text_to_sound_v2",
  "output_format": "mp3_44100_128",
  "character_cost": 100
}
```

Top-level structure is a JSON array. New entries are appended. Do not delete entries — `sfx-librarian` depends on full history for uniqueness reasoning.

---

## User Flow

```
/sfx-generate stinger 5
        ↓
sfx-writer reads AGENTS.md + generation_log.json
        ↓
Reasons over history → assigns 5 unique sonic angles
        ↓
Writes 5 ElevenLabs prompts (max 1,000 chars each)
        ↓
Council debates each prompt (sfx-ear, sfx-director, sfx-librarian)
        ↓
Revision rounds if needed (max 2) → sfx-writer has final decision
        ↓
generate.py — ElevenLabs API call + download (throttled by tier)
        ↓
organizer.py — auto-name + route to sfx_library/stingers/
        ↓
generation_log.json updated
```

---

## Commands

| Command | What it does |
|---|---|
| `/sfx-generate [category] [qty]` | Generate N SFX of a given category |
| `/sfx-batch` | Queue multiple category requests and run as one batch |
| `/sfx-library` | Browse the current SFX pool by category |

Categories: `ambience`, `stinger`, `transition`, `background_music`, `foley`, `jingle`, `news`, `misc`

---

## Naming Convention

Auto-generated by `organizer.py`. Format:

```
[category]_[sonic_descriptor]_[mood]_[index].mp3
```

Examples:
```
stinger_brass_punchy_001.mp3
ambience_rain_interior_002.mp3
news_electronic_rising_003.mp3
```

Index is zero-padded and scoped per category folder.

---

## Key Files to Author

| File | Purpose |
|---|---|
| `AGENTS.md` | Full project context, council rules, folder map, naming spec, revision cap |
| `opencode.json` | Agent config — model, mode, permissions, temperature per agent |
| `.opencode/agents/sfx-writer.md` | Writer system prompt — pipeline orchestration logic |
| `.opencode/agents/sfx-ear.md` | Ear critic system prompt |
| `.opencode/agents/sfx-director.md` | Director critic system prompt |
| `.opencode/agents/sfx-librarian.md` | Librarian critic system prompt |
| `.opencode/commands/sfx-generate.md` | `/sfx-generate` command template |
| `scripts/generate.py` | ElevenLabs API integration + download handler |
| `scripts/organizer.py` | Auto-naming + folder routing logic |

---

## Environment Variables

```
ELEVENLABS_API_KEY=
```

Set in `.env` at repo root. Never commit to Git. All model access is configured inside OpenCode via `opencode.json` — no additional API keys needed.

---

## Notes

- OpenCode is the harness, TUI, and multi-agent runtime — no external orchestration framework needed
- `sfx-writer` is the orchestrator with final decision authority — council informs, writer decides
- Council max 2 revision rounds is a hard cap enforced in `AGENTS.md` to control token cost
- `generation_log.json` is long-term memory — do not delete entries or uniqueness reasoning breaks
- Uniqueness is fully agent-based — no embedding scripts, no external similarity libraries
- Manual prompt override is always available as last resort inside the TUI