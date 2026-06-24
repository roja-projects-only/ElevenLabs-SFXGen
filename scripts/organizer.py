#!/usr/bin/env python3
"""CLI entrypoint for organising a single generated sound-effect file.

Moves an audio file into the library with a canonical name and prints the
resulting filename, id, and path.

Usage
-----
    python scripts/organizer.py --src /tmp/thunder.mp3 --category ambience \
        --descriptor rain --mood interior

Exit codes
----------
0   Success
1   Organisation failure (invalid category, missing file, etc.)
"""

from __future__ import annotations

import argparse
import json
import sys

from sfx_studio.config import CATEGORIES
from sfx_studio.organizer import organize


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="organizer.py",
        description="Name and move a generated SFX file into the library.",
    )
    parser.add_argument("--src", required=True, help="Path to the generated audio file")
    parser.add_argument(
        "--category",
        required=True,
        choices=CATEGORIES,
        help="SFX category",
    )
    parser.add_argument("--descriptor", required=True,
                        help="Sonic descriptor (e.g. brass, rain, electronic)")
    parser.add_argument("--mood", required=True,
                        help="Mood / affect (e.g. punchy, interior, rising)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Parse args, organise file, print result as JSON.

    Returns exit code for ``sys.exit``.
    """
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1

    try:
        filename, identifier, output_path = organize(
            src_path=args.src,
            category=args.category,
            descriptor=args.descriptor,
            mood=args.mood,
        )
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    result = {
        "filename": filename,
        "id": identifier,
        "output_path": str(output_path),
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
