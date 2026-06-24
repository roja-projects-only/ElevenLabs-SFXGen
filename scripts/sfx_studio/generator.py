"""Asynchronous ElevenLabs Sound Effects API client.

Uses ``AsyncElevenLabs`` to submit one or more text-to-sound-effects requests
concurrently, respecting the account tier's concurrency limit via
``asyncio.Semaphore``.

Sentinel discipline
-------------------
Parameters ``duration_seconds``, ``loop``, ``prompt_influence``, and
``model_id`` use a local ``_OMIT`` sentinel.  When the value is ``_OMIT`` the
keyword is **not** passed to the SDK at all — this is the correct way to let
the API use its defaults (especially for ``duration_seconds`` where ``None`` is
*not* the same as omitting the parameter).
"""

from __future__ import annotations

import asyncio
import contextlib
from pathlib import Path
from typing import Any

import httpx

from .config import DEFAULT_OUTPUT_FORMAT, load_env

# ---------------------------------------------------------------------------
# Sentinel — marks parameters that should be omitted from the SDK call rather
# than passed as ``None``.
# ---------------------------------------------------------------------------

_OMIT: object = object()


# ---------------------------------------------------------------------------
# Parameter builder (single source of truth for omission discipline)
# ---------------------------------------------------------------------------

def _build_convert_params(
    text: str,
    *,
    duration_seconds: object = _OMIT,
    loop: object = _OMIT,
    prompt_influence: object = _OMIT,
    model_id: object = _OMIT,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
) -> dict[str, Any]:
    """Build the kwargs dict for ``client.text_to_sound_effects.convert``.

    Only parameters whose value is **not** ``_OMIT`` are included.  This is
    critical because the ElevenLabs SDK distinguishes between a parameter
    omitted entirely and a parameter set to ``None`` (especially for
    ``duration_seconds``).
    """
    params: dict[str, Any] = {"text": text, "output_format": output_format}

    if duration_seconds is not _OMIT:
        params["duration_seconds"] = duration_seconds
    if loop is not _OMIT:
        params["loop"] = loop
    if prompt_influence is not _OMIT:
        params["prompt_influence"] = prompt_influence
    if model_id is not _OMIT:
        params["model_id"] = model_id

    return params


# ---------------------------------------------------------------------------
# Client factory
# ---------------------------------------------------------------------------

def make_client() -> Any:
    """Create and return an ``AsyncElevenLabs()`` client.

    Calls :func:`load_env` first so that ``ELEVENLABS_API_KEY`` is available
    from ``.env``.
    """
    from elevenlabs import AsyncElevenLabs  # noqa: PLC0415

    load_env()
    return AsyncElevenLabs()


# ---------------------------------------------------------------------------
# Single generation
# ---------------------------------------------------------------------------

async def generate_one(
    client: Any,
    text: str,
    output_path: str | Path,
    *,
    prompt_influence: object = _OMIT,
    duration_seconds: object = _OMIT,
    loop: object = _OMIT,
    model_id: object = _OMIT,
    output_format: str = DEFAULT_OUTPUT_FORMAT,
    semaphore: asyncio.Semaphore | None = None,
) -> Path:
    """Generate a single sound effect and write it to *output_path*.

    Parameters
    ----------
    client : AsyncElevenLabs
        An authenticated async client instance.
    text : str
        Prompt describing the sound effect.
    output_path : str | Path
        Where the MP3 (or other format) will be written.
    prompt_influence : float, optional
        How closely to follow the prompt (0–1).  Omitted if not provided.
    duration_seconds : float, optional
        Fixed duration.  Omitted (auto) if not provided.
    loop : bool, optional
        Generate a seamless loop.  Omitted if not provided.
    model_id : str, optional
        Model override.  Omitted if not provided (uses SDK default).
    output_format : str
        Output audio format string.
    semaphore : asyncio.Semaphore, optional
        Concurrency limiter.  Acquired before the API call if given.

    Returns
    -------
    Path
        The resolved *output_path* on success.

    Raises
    ------
    RuntimeError
        On API errors (401, 425, network, timeout, or generic HTTP failure).
    ValueError
        On 422 (invalid parameters).
    """
    output_path_obj = Path(output_path)
    params = _build_convert_params(
        text=text,
        prompt_influence=prompt_influence,
        duration_seconds=duration_seconds,
        loop=loop,
        model_id=model_id,
        output_format=output_format,
    )

    # ``nullcontext`` lets us use a single ``async with`` whether or not a
    # semaphore was supplied, and guarantees the limiter is released even if
    # the API call is cancelled mid-acquire (fixes a theoretical leak).
    limiter = semaphore if semaphore is not None else contextlib.nullcontext()
    try:
        async with limiter:
            audio_iterator = client.text_to_sound_effects.convert(**params)
            with open(output_path_obj, "wb") as f:
                async for chunk in audio_iterator:
                    f.write(chunk)
    except Exception as exc:
        # Map known ElevenLabs / HTTP errors to clean Python exceptions.
        _reraise_mapped(exc)

    return output_path_obj.resolve()


# ---------------------------------------------------------------------------
# Batched generation
# ---------------------------------------------------------------------------

async def generate_batch(
    items: list[dict[str, Any]],
    *,
    concurrency: int = 2,
    client: Any = None,
) -> list[Path | BaseException]:
    """Generate multiple sound effects concurrently.

    Parameters
    ----------
    items : list[dict]
        Each dict must contain ``text`` and ``output_path``.  Optional keys:
        ``prompt_influence``, ``duration_seconds``, ``loop``, ``model_id``,
        ``output_format``.
    concurrency : int
        Max concurrent API requests (default 2 — Free tier).  Should match
        the account tier.
    client : AsyncElevenLabs, optional
        Reusable client.  Created via :func:`make_client` if ``None``.

    Returns
    -------
    list[Path | BaseException]
        One result per item — either the resolved ``Path`` on success or the
        exception that was raised.  One failure does **not** cancel the rest
        of the batch.
    """
    if client is None:
        client = make_client()

    sem = asyncio.Semaphore(concurrency)

    async def _task(item: dict[str, Any]) -> Path:
        return await generate_one(
            client,
            text=item["text"],
            output_path=item["output_path"],
            prompt_influence=item.get("prompt_influence", _OMIT),
            duration_seconds=item.get("duration_seconds", _OMIT),
            loop=item.get("loop", _OMIT),
            model_id=item.get("model_id", _OMIT),
            output_format=item.get("output_format", DEFAULT_OUTPUT_FORMAT),
            semaphore=sem,
        )

    # ``return_exceptions=True`` keeps one failure from cancelling the batch;
    # each result is either the resolved Path or the exception that was raised.
    return await asyncio.gather(
        *(_task(item) for item in items), return_exceptions=True
    )


# ---------------------------------------------------------------------------
# Error mapping
# ---------------------------------------------------------------------------

def _reraise_mapped(exc: Exception) -> None:
    """Re-raise *exc* as a more specific exception type based on ElevenLabs
    error classes."""
    from elevenlabs import errors as el_errors  # noqa: PLC0415

    if isinstance(exc, el_errors.UnauthorizedError):
        raise RuntimeError(
            "Invalid ElevenLabs API key (401). Check ELEVENLABS_API_KEY — "
            "use the setup-api-key skill."
        ) from exc
    if isinstance(exc, el_errors.UnprocessableEntityError):
        raise ValueError(f"ElevenLabs rejected the request (422): {exc}") from exc
    if isinstance(exc, el_errors.TooEarlyError):
        raise RuntimeError(
            "ElevenLabs rate limit reached (425). Wait and retry."
        ) from exc
    if isinstance(exc, httpx.TimeoutException):
        raise RuntimeError("ElevenLabs request timed out. Retry.") from exc
    if isinstance(exc, httpx.ConnectError):
        raise RuntimeError(
            "Could not connect to ElevenLabs. Check your network."
        ) from exc
    if isinstance(exc, httpx.HTTPStatusError):
        raise RuntimeError(f"ElevenLabs HTTP error: {exc}") from exc
    # Unknown exception type — re-raise as-is.
    raise
