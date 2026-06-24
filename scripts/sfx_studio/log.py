"""Read, append, and build entries for ``generation_log.json``.

All log access is serialized via a module-level ``threading.Lock`` so that
concurrent in-process callers (e.g. batched generation) do not corrupt the
file.  Cross-process callers are **not** protected — use the CLI entrypoints
serially or accept the small risk of interleaved writes.

Public functions
----------------
read_log() -> list[dict]
    Load every entry from the log file.  Returns ``[]`` if missing / invalid.
append_entry(entry: dict) -> None
    Atomically append *entry* to the log array (thread-safe).
build_entry(...) -> dict
    Construct a complete 15-field entry object ready for serialisation.
"""

from __future__ import annotations

import json
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import CATEGORIES, DEFAULT_MODEL_ID, DEFAULT_OUTPUT_FORMAT, LOG_PATH

# ---------------------------------------------------------------------------
# Module-level lock — serialises all read-modify-write access within one
# Python process.
# ---------------------------------------------------------------------------

_log_lock = threading.Lock()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_log() -> list[dict[str, Any]]:
    """Return every entry currently in the generation log.

    If the file does not exist, is empty, or contains invalid JSON, an empty
    list is returned **without** raising.  This supports "create-on-write"
    semantics.
    """
    try:
        raw = LOG_PATH.read_text(encoding="utf-8")
    except (FileNotFoundError, OSError):
        return []

    raw = raw.strip()
    if not raw:
        return []

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    if isinstance(data, list):
        return data
    return []


def append_entry(entry: dict[str, Any]) -> None:
    """Atomically append *entry* to the log file.

    The operation is serialised by a ``threading.Lock`` and uses a
    temporary-file + ``os.replace`` to avoid partial writes corrupting the
    log.

    Parameters
    ----------
    entry : dict
        A full 15-field entry (typically produced by :func:`build_entry`).
    """
    with _log_lock:
        # Ensure the logs/ directory exists.
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        entries = read_log()
        entries.append(entry)

        # Write to a temporary file in the same directory, then atomically
        # replace the real log file.  This prevents partial-write corruption.
        fd, tmp_path_str = tempfile.mkstemp(
            suffix=".json",
            prefix="generation_log_",
            dir=str(LOG_PATH.parent),
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as tmp_fh:
                json.dump(entries, tmp_fh, indent=2, ensure_ascii=False)
                tmp_fh.flush()
                os.fsync(tmp_fh.fileno())
            os.replace(tmp_path_str, str(LOG_PATH))
        except BaseException:
            # Clean up the temp file on any error before re-raising.
            try:
                os.unlink(tmp_path_str)
            except OSError:
                pass
            raise


def build_entry(
    *,
    identifier: str,
    prompt: str,
    category: str,
    sonic_angles: dict[str, str],
    duration_seconds: float | None,
    prompt_influence: float | None,
    output_filename: str,
    output_path: str,
    council_scores: dict[str, int],
    council_notes: dict[str, str],
    revision_count: int,
    model_id: str = DEFAULT_MODEL_ID,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
) -> dict[str, Any]:
    """Construct a complete generation-log entry.

    Parameters
    ----------
    identifier : str
        Log entry id (filename without extension, e.g. ``stinger_brass_punchy_001``).
    prompt : str
        The ElevenLabs prompt text.
    category : str
        One of :data:`CATEGORIES`.
    sonic_angles : dict[str, str]
        Five-dimension sonic fingerprint (instrumentation, attack, texture,
        spatial, frequency).
    duration_seconds : float | None
        Fixed duration or ``None`` for auto.
    prompt_influence : float | None
        Prompt adherence value.
    output_filename : str
        Final filename (e.g. ``stinger_brass_punchy_001.mp3``).
    output_path : str
        Relative path from repo root (e.g. ``sfx_library/stingers/...``).
    council_scores : dict[str, int]
        Critic scores keyed by agent name.
    council_notes : dict[str, str]
        Critic rationales keyed by agent name.
    revision_count : int
        Number of revision rounds (0, 1, or 2).
    model_id : str
        ElevenLabs model identifier.
    output_format : str
        Audio output format string.

    Returns
    -------
    dict
        The complete 15-field entry.

    Raises
    ------
    ValueError
        If *category* is not recognised.
    """
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Valid: {', '.join(CATEGORIES)}"
        )

    # character_cost: auto = 100 flat, fixed = 25 * duration_seconds
    if duration_seconds is None:
        character_cost = 100
    else:
        character_cost = 25 * duration_seconds

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "id": identifier,
        "prompt": prompt,
        "category": category,
        "sonic_angles": sonic_angles,
        "duration_seconds": duration_seconds,
        "prompt_influence": prompt_influence,
        "output_filename": output_filename,
        "output_path": output_path,
        "council_scores": council_scores,
        "council_notes": council_notes,
        "revision_count": revision_count,
        "timestamp": timestamp,
        "model_id": model_id,
        "output_format": output_format,
        "character_cost": character_cost,
    }
