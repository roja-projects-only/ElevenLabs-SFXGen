"""Auto-naming and folder routing for generated sound-effect files.

After ElevenLabs returns an audio file, :func:`organize` assigns it a
canonical name per the project naming convention, moves it into the
appropriate category folder under ``sfx_library/``, and returns the final
filename, id (stem), and path.

Naming convention
-----------------
``[category]_[sonic_descriptor]_[mood]_[index].mp3``

Index is zero-padded, three-digit, scoped per category folder.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from .config import CATEGORIES, CATEGORY_FOLDERS, LIBRARY_ROOT


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _assign_name(
    category: str,
    descriptor: str,
    mood: str,
) -> tuple[str, str, Path]:
    """Compute the next available filename for a new SFX in *category*.

    Scans ``LIBRARY_ROOT / <category_folder> / *.mp3``, finds the highest
    existing index, increments by one, and returns the components.

    Returns
    -------
    (filename, id_stem, full_output_path)
        e.g. ``("stinger_brass_punchy_001.mp3", "stinger_brass_punchy_001",
        Path(".../sfx_library/stingers/stinger_brass_punchy_001.mp3"))``
    """
    folder_name = CATEGORY_FOLDERS[category]
    target_dir = LIBRARY_ROOT / folder_name
    target_dir.mkdir(parents=True, exist_ok=True)

    # Scan existing files for the highest index.
    max_index = 0
    pattern = re.compile(rf"^{re.escape(category)}_{re.escape(descriptor)}_{re.escape(mood)}_(\d+)\.mp3$")
    for f in target_dir.glob("*.mp3"):
        m = pattern.match(f.name)
        if m:
            idx = int(m.group(1))
            if idx > max_index:
                max_index = idx

    # Increment and try; defend against races / collisions.
    for attempt in range(100):
        index = max_index + 1 + attempt
        filename = f"{category}_{descriptor}_{mood}_{index:03d}.mp3"
        output_path = target_dir / filename
        if not output_path.exists():
            return filename, filename[:-4], output_path

    # Extremely unlikely — 100 consecutive collisions.
    raise FileExistsError(
        f"Could not find unused index in {target_dir} after 100 attempts"
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def organize(
    src_path: str | Path,
    category: str,
    descriptor: str,
    mood: str,
) -> tuple[str, str, Path]:
    """Name and move a generated audio file into the library.

    Parameters
    ----------
    src_path : str | Path
        Path to the generated MP3 (or other format) file.
    category : str
        One of :data:`CATEGORIES`.
    descriptor : str
        Sonic descriptor — the dominant instrumentation / source.
    mood : str
        Affect / mood of the sound.

    Returns
    -------
    (filename, id_stem, output_path)
        e.g. ``("stinger_brass_punchy_001.mp3", "stinger_brass_punchy_001",
        WindowsPath(".../sfx_library/stingers/stinger_brass_punchy_001.mp3"))``

    Raises
    ------
    ValueError
        If *category* is not recognised.
    FileNotFoundError
        If *src_path* does not exist.
    """
    if category not in CATEGORIES:
        raise ValueError(
            f"Unknown category {category!r}. Valid: {', '.join(CATEGORIES)}"
        )

    src = Path(src_path)
    if not src.is_file():
        raise FileNotFoundError(f"Source file not found: {src}")

    filename, identifier, output_path = _assign_name(category, descriptor, mood)

    shutil.move(str(src), str(output_path))

    return filename, identifier, output_path
