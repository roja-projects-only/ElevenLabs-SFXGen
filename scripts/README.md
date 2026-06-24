# SFX Studio — Scripts

Python package and CLI entrypoints for generating and organising sound effects
via the ElevenLabs Sound Effects API.

## Quick Start

```bash
# Install dependencies
pip install -r scripts/requirements.txt

# Set your API key (or use the setup-api-key skill in OpenCode)
# echo "ELEVENLABS_API_KEY=sk_..." > .env
```

## CLI Commands

### Generate a single sound effect

```bash
python scripts/generate.py \
    --text "Thunder rumbling in the distance with light rain" \
    --category ambience \
    --out /tmp/thunder.mp3 \
    --tier free
```

Optional parameters:
- `--prompt-influence 0.7` — how closely to follow the prompt (0–1)
- `--duration 3.0` — fixed duration in seconds (omit for auto, which is cheaper)
- `--loop` — generate a seamless loop (MP3 only)
- `--output-format mp3_44100_128` — audio format
- `--model-id eleven_text_to_sound_v2` — model override

### Organise a generated file into the library

```bash
python scripts/organizer.py \
    --src /tmp/thunder.mp3 \
    --category ambience \
    --descriptor rain \
    --mood interior
```

Prints a JSON object with the assigned `filename`, `id`, and `output_path`.

## Package Layout

```
scripts/
├── README.md
├── requirements.txt
├── generate.py          # CLI: generate a sound effect
├── organizer.py         # CLI: name & move into library
└── sfx_studio/          # Reusable package
    ├── __init__.py
    ├── config.py        # Paths, constants, env loader
    ├── log.py           # generation_log.json read/append
    ├── generator.py     # Async ElevenLabs client
    └── organizer.py     # Naming & folder routing
```

## Concurrency Notes

- The `asyncio.Semaphore` in `sfx_studio.generator` limits concurrent API
  requests **within a single Python process**.
- Concurrent CLI invocations across processes are **not** throttled — execute
  them serially if you need strict adherence to your tier limit.

## API Key

The API key is read from `.env` at the repository root via `python-dotenv`.
Use the `setup-api-key` skill inside OpenCode to configure it safely, or
manually create a `.env` file with:

```
ELEVENLABS_API_KEY=sk_your_key_here
```
