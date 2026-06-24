#!/usr/bin/env python3
"""CLI entrypoint for batch-generating multiple sound effects.

Usage
-----
    python scripts/generate_batch.py --input batch.json [--tier free]

Input JSON format
-----------------
    {
      "tier": "free",
      "items": [
        {
          "text": "required — ElevenLabs prompt (≤1000 chars)",
          "category": "required — one of the 8 categories",
          "descriptor": "required — sonic descriptor (e.g. brass, rain)",
          "mood": "required — mood (e.g. punchy, interior)",
          "prompt_influence": "optional — float or omit key entirely",
          "duration_seconds": "optional — float or omit key entirely",
          "loop": "optional — boolean or omit key entirely",
          "model_id": "optional — string or omit key entirely",
          "output_format": "optional — string, defaults to mp3_44100_128"
        }
      ]
    }

    Omit optional keys entirely (don't set to null) — the script uses a
    sentinel to skip them at the API level.

Exit codes
----------
0   All items succeeded
1   One or more items failed
2   Invalid input (missing file, bad JSON, no items)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

from sfx_studio.config import (
    CATEGORIES,
    DEFAULT_OUTPUT_FORMAT,
    LIBRARY_ROOT,
    REPO_ROOT,
    TIER_CONCURRENCY,
    get_concurrency,
    load_env,
)
from sfx_studio.generator import _OMIT, generate_one, make_client
from sfx_studio.organizer import organize


def _to_sentinel(value: object) -> object:
    """Convert ``None`` (missing key or JSON null) to ``_OMIT``; pass other values as-is."""
    return _OMIT if value is None else value


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="generate_batch.py",
        description="Batch-generate multiple sound effects from a JSON specification.",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to batch JSON file",
    )
    parser.add_argument(
        "--tier",
        default=None,
        help="ElevenLabs account tier (overrides tier in JSON). Valid: "
        + ", ".join(sorted(TIER_CONCURRENCY)),
    )

    args = parser.parse_args(argv)

    # Validate tier if provided via CLI
    if args.tier is not None:
        try:
            get_concurrency(args.tier)
        except ValueError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            parser.exit(2)

    return args


def _load_batch(path: str, tier_override: str | None) -> tuple[str, list[dict[str, Any]]]:
    """Load and validate the batch JSON file.

    Returns ``(tier, items)``.  Raises ``ValueError`` on validation failure.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        raise ValueError(f"Input file not found: {path}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}")

    if not isinstance(data, dict):
        raise ValueError("Batch file must contain a JSON object")

    # Resolve tier: CLI override > JSON tier > default "free"
    tier = tier_override if tier_override is not None else data.get("tier", "free")

    # Validate tier
    try:
        get_concurrency(tier)
    except ValueError:
        raise ValueError(f"Unknown tier {tier!r} in batch file")

    items = data.get("items")
    if not isinstance(items, list):
        raise ValueError("Batch file must contain an 'items' array")
    if not items:
        raise ValueError("Batch file 'items' array is empty")

    # Validate every item's required fields up front
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValueError(f"Item {i} is not a JSON object")
        for field in ("text", "category", "descriptor", "mood"):
            if field not in item or not isinstance(item.get(field), str):
                raise ValueError(f"Item {i} is missing required field '{field}'")
        if item["category"] not in CATEGORIES:
            raise ValueError(
                f"Item {i}: unknown category '{item['category']}'. "
                f"Valid: {', '.join(CATEGORIES)}"
            )

    return tier, items


async def _process_item(
    client: Any,
    sem: asyncio.Semaphore,
    item: dict[str, Any],
    tmp_dir: Path,
) -> dict[str, Any]:
    """Generate and organise a single batch item.

    Returns a result dict with ``"status": "ok"`` or ``"status": "error"``.
    """
    temp_path = tmp_dir / f"batch_{uuid.uuid4().hex}.mp3"

    # Step 1 — generate audio to a temp file
    try:
        await generate_one(
            client,
            text=item["text"],
            output_path=temp_path,
            prompt_influence=_to_sentinel(item.get("prompt_influence")),
            duration_seconds=_to_sentinel(item.get("duration_seconds")),
            loop=_to_sentinel(item.get("loop")),
            model_id=_to_sentinel(item.get("model_id")),
            output_format=item.get("output_format", DEFAULT_OUTPUT_FORMAT),
            semaphore=sem,
        )
    except Exception as exc:
        # Generation failed.  If the temp file exists despite the error, leave
        # it for debugging.
        if temp_path.exists():
            print(
                f"[debug] Temp file left for inspection: {temp_path}",
                file=sys.stderr,
            )
        return {
            "text": item["text"],
            "status": "error",
            "error": str(exc),
        }

    # Step 2 — organise (move temp file to its final library location)
    try:
        filename, identifier, output_path = organize(
            src_path=temp_path,
            category=item["category"],
            descriptor=item["descriptor"],
            mood=item["mood"],
        )
    except Exception as exc:
        # Organise failed — temp file still exists, leave for debugging.
        print(
            f"[debug] Temp file left for inspection: {temp_path}",
            file=sys.stderr,
        )
        return {
            "text": item["text"],
            "status": "error",
            "error": str(exc),
        }

    return {
        "text": item["text"],
        "status": "ok",
        "filename": filename,
        "id": identifier,
        "output_path": output_path.relative_to(REPO_ROOT).as_posix(),
    }


async def _run(tier: str, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Run the full batch: create client, semaphore, process all items."""
    load_env()
    client = make_client()
    sem = asyncio.Semaphore(get_concurrency(tier))

    tmp_dir = LIBRARY_ROOT / "_tmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    try:
        results = await asyncio.gather(
            *(_process_item(client, sem, item, tmp_dir) for item in items),
        )
    finally:
        _cleanup_tmp(tmp_dir)

    return results


def _cleanup_tmp(tmp_dir: Path) -> None:
    """Remove the temp directory if empty, otherwise warn."""
    if not tmp_dir.exists():
        return
    try:
        remaining = list(tmp_dir.iterdir())
        if not remaining:
            tmp_dir.rmdir()
        else:
            print(
                f"[debug] {len(remaining)} temp file(s) remain in {tmp_dir}",
                file=sys.stderr,
            )
    except OSError as exc:
        print(f"[debug] Could not clean up {tmp_dir}: {exc}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Parse args, load batch, generate all items, print result JSON.

    Returns exit code for ``sys.exit``.
    """
    try:
        args = _parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2

    # Load and validate the batch file.
    try:
        tier, items = _load_batch(args.input, args.tier)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    # Run the batch.
    try:
        results = asyncio.run(_run(tier, items))
    except (ValueError, RuntimeError, FileNotFoundError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    # Build and print output summary.
    succeeded = sum(1 for r in results if r["status"] == "ok")
    failed = len(results) - succeeded
    output = {
        "results": results,
        "summary": f"{len(results)} attempted, {succeeded} succeeded, {failed} failed",
    }
    print(json.dumps(output, indent=2))

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
