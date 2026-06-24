"""Estimate token usage for Markdown context files.

Token counts are an estimate of how much of an AI agent's context window a file
will consume. Accurate counts use ``tiktoken`` when it is installed; otherwise a
simple ``character_count / 4`` heuristic is used.
"""

from __future__ import annotations

_CHARS_PER_TOKEN = 4
_ENCODING = "cl100k_base"

# Cache the encoder so repeated calls do not re-load it.
_encoder = None
_tiktoken_checked = False


def _get_encoder():
    """Return a cached tiktoken encoder, or ``None`` if tiktoken is missing."""
    global _encoder, _tiktoken_checked
    if _tiktoken_checked:
        return _encoder
    _tiktoken_checked = True
    try:
        import tiktoken

        _encoder = tiktoken.get_encoding(_ENCODING)
    except Exception:
        _encoder = None
    return _encoder


def _heuristic(text: str) -> int:
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in *text*.

    Uses ``tiktoken`` when available for an accurate count, and falls back to a
    ``len(text) // 4`` heuristic otherwise.
    """
    if not text:
        return 0
    encoder = _get_encoder()
    if encoder is None:
        return _heuristic(text)
    try:
        return len(encoder.encode(text))
    except Exception:
        return _heuristic(text)


def using_tiktoken() -> bool:
    """Return True if accurate tiktoken counting is available."""
    return _get_encoder() is not None
