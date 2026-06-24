"""SFX Studio — modular package for managing sound-effect generation and organization.

Public API re-exported from submodules:
    - config:       Paths, constants, env loader, concurrency lookup
    - log:          generation_log.json read/append/build_entry
    - generator:    ElevenLabs API client, generate_one, generate_batch
    - organizer:    File naming, folder routing, file move
"""

from .config import (
    CATEGORIES,
    CATEGORY_FOLDERS,
    DEFAULT_MODEL_ID,
    DEFAULT_OUTPUT_FORMAT,
    ENV_PATH,
    LIBRARY_ROOT,
    LOG_PATH,
    REPO_ROOT,
    TIER_CONCURRENCY,
    get_concurrency,
    load_env,
)
from .log import append_entry, build_entry, read_log
from .generator import generate_batch, generate_one, make_client
from .organizer import organize

__all__ = [
    # config
    "REPO_ROOT",
    "LIBRARY_ROOT",
    "LOG_PATH",
    "ENV_PATH",
    "CATEGORIES",
    "CATEGORY_FOLDERS",
    "TIER_CONCURRENCY",
    "DEFAULT_OUTPUT_FORMAT",
    "DEFAULT_MODEL_ID",
    "get_concurrency",
    "load_env",
    # log
    "read_log",
    "append_entry",
    "build_entry",
    # generator
    "generate_one",
    "generate_batch",
    "make_client",
    # organizer
    "organize",
]
