#!/usr/bin/env python3
"""CLI entrypoint for generating a single sound effect.

Usage
-----
    python scripts/generate.py --text "Thunder rumble" --category ambience \
        --out /tmp/thunder.mp3 [--prompt-influence 0.5] [--duration 3.0] \
        [--loop] [--output-format mp3_44100_128] [--model-id eleven_text_to_sound_v2] \
        [--tier free]

Exit codes
----------
0   Success
1   Generation failure (API error, network error, etc.)
2   Invalid arguments (unknown category, tier, etc.)
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from sfx_studio.config import CATEGORIES, TIER_CONCURRENCY, get_concurrency, load_env
from sfx_studio.generator import generate_one, make_client
from sfx_studio.generator import _OMIT  # sentinel for omitted optional params


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate.py",
        description="Generate a sound effect via the ElevenLabs API and save it to disk.",
    )
    parser.add_argument("--text", required=True, help="Prompt text for the sound effect")
    parser.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help="SFX category (determines folder routing after organise)",
    )
    parser.add_argument("--prompt-influence", type=float, default=None,
                        help="How closely to follow the prompt (0–1)")
    parser.add_argument("--duration", type=float, default=None,
                        help="Fixed duration in seconds (omit for auto)")
    parser.add_argument("--loop", action="store_true", default=_OMIT,
                        help="Generate a seamless loop (omit by default)")
    parser.add_argument("--output-format", default="mp3_44100_128",
                        help="Audio output format (default: mp3_44100_128)")
    parser.add_argument("--model-id", default=None,
                        help="Model override (omit for SDK default)")
    parser.add_argument(
        "--tier",
        default="free",
        help="ElevenLabs account tier (default: free). Valid: "
             + ", ".join(sorted(TIER_CONCURRENCY)),
    )
    parser.add_argument("--out", required=True,
                        help="Output file path for the generated audio")

    args = parser.parse_args(argv)

    # Validate tier
    try:
        get_concurrency(args.tier)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        parser.exit(2)

    return args


def _to_sentinel(value: object) -> object:
    """Convert ``None`` (from CLI default) to ``_OMIT``; pass other values as-is."""
    return _OMIT if value is None else value


async def _run(args: argparse.Namespace) -> None:
    load_env()
    client = make_client()
    sem = asyncio.Semaphore(get_concurrency(args.tier))

    result = await generate_one(
        client,
        text=args.text,
        output_path=args.out,
        prompt_influence=_to_sentinel(args.prompt_influence),
        duration_seconds=_to_sentinel(args.duration),
        loop=args.loop,
        model_id=_to_sentinel(args.model_id),
        output_format=args.output_format,
        semaphore=sem,
    )
    print(result)


def main(argv: list[str] | None = None) -> int:
    """Parse args, generate, print result path on success.

    Returns exit code for ``sys.exit``.
    """
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    try:
        asyncio.run(_run(args))
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
