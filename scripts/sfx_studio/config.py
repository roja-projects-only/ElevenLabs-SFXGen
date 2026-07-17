"""Paths, constants, environment loader for SFX Studio.

This module has NO dependency on ``elevenlabs`` so it can always be imported
safely, even when the SDK is not installed.

Constants
---------
REPO_ROOT : Path
    Repository root discovered by walking upward for a sentinel file.
LIBRARY_ROOT : Path
    ``REPO_ROOT / "sfx_library"``
LOG_PATH : Path
    ``REPO_ROOT / "logs" / "generation_log.json"``
ENV_PATH : Path
    ``REPO_ROOT / ".env"``
CATEGORIES : tuple[str, ...]
    Valid sound-effect categories.
CATEGORY_FOLDERS : dict[str, str]
    Mapping from category name to its plural folder name under ``sfx_library/``.
TIER_CONCURRENCY : dict[str, int]
    ElevenLabs API concurrency limits per account tier.

Functions
---------
get_concurrency(tier: str) -> int
    Look up the concurrency limit for *tier*.
load_env() -> None
    Load environment variables from ``.env`` (uses ``python-dotenv``).
"""

from __future__ import annotations

from pathlib import Path


# ---------------------------------------------------------------------------
# Repository root discovery
# ---------------------------------------------------------------------------

def _discover_repo_root() -> Path:
    """Walk upward from this file looking for a sentinel file (AGENTS.md or
    opencode.json).  If none is found, fall back to the grandparent of
    ``scripts/sfx_studio/`` (i.e. the repo root)."""
    candidate = Path(__file__).resolve().parent.parent.parent  # scripts/
    sentinels = ("AGENTS.md", "opencode.json")
    for parent in [candidate, *candidate.parents]:
        if any((parent / s).is_file() for s in sentinels):
            return parent
    return candidate


REPO_ROOT: Path = _discover_repo_root()

# ---------------------------------------------------------------------------
# Derived paths
# ---------------------------------------------------------------------------

LIBRARY_ROOT: Path = REPO_ROOT / "sfx_library"
LOG_PATH: Path = REPO_ROOT / "logs" / "generation_log.json"
ENV_PATH: Path = REPO_ROOT / ".env"

# ---------------------------------------------------------------------------
# Category constants
# ---------------------------------------------------------------------------

CATEGORIES: tuple[str, ...] = (
    "ambience",
    "stinger",
    "transition",
    "background_music",
    "foley",
    "jingle",
    "news",
    "misc",
)

CATEGORY_FOLDERS: dict[str, str] = {
    "ambience": "ambience",
    "stinger": "stingers",
    "transition": "transitions",
    "background_music": "background_music",
    "foley": "foley",
    "jingle": "jingles",
    "news": "news",
    "misc": "misc",
}

# ---------------------------------------------------------------------------
# ElevenLabs constants
# ---------------------------------------------------------------------------

TIER_CONCURRENCY: dict[str, int] = {
    "free": 2,
    "starter": 3,
    "creator": 5,
    "pro": 10,
}

DEFAULT_OUTPUT_FORMAT: str = "mp3_44100_128"
DEFAULT_MODEL_ID: str = "eleven_text_to_sound_v2"


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------

def get_concurrency(tier: str) -> int:
    """Return the maximum concurrent requests allowed for *tier*.

    Parameters
    ----------
    tier : str
        Account tier name (case-insensitive).

    Returns
    -------
    int
        Concurrency limit.

    Raises
    ------
    ValueError
        If *tier* is not one of the known tiers.
    """
    key = tier.lower()
    try:
        return TIER_CONCURRENCY[key]
    except KeyError:
        valid = ", ".join(sorted(TIER_CONCURRENCY))
        raise ValueError(
            f"Unknown tier {tier!r}. Valid options: {valid}"
        ) from None


def load_env() -> None:
    """Load environment variables from ``.env`` (uses ``python-dotenv``).

    This is safe to call multiple times; ``load_dotenv`` is idempotent.
    """
    from dotenv import load_dotenv  # noqa: PLC0415 — lazy import

    load_dotenv(ENV_PATH)
