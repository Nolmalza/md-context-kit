"""Estimate token usage for Markdown context files.

Accurate counts use ``tiktoken`` when it is installed. The fallback is no
longer a flat ``chars / 4``: that heuristic is badly wrong for Thai, measured on
real project docs (pure Thai prose ≈ 0.96 tokens per character, mixed
Thai/English/code docs ≈ 0.25). The fallback therefore weights Thai codepoints
separately, so a Thai-heavy document is not under-counted by roughly 4x.
"""

from __future__ import annotations

_CHARS_PER_TOKEN_LATIN = 4.0
_TOKENS_PER_THAI_CHAR = 0.96
_ENCODING = "cl100k_base"

# Thai block. Thai characters cost ~1 token each in cl100k_base, unlike Latin
# text at ~4 characters per token.
_THAI_START = 0x0E00
_THAI_END = 0x0E7F

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


def thai_char_count(text: str) -> int:
    """Number of Thai-block characters in *text*."""
    return sum(1 for ch in text if _THAI_START <= ord(ch) <= _THAI_END)


def thai_ratio(text: str) -> float:
    """Share of characters that are Thai (0.0 - 1.0)."""
    if not text:
        return 0.0
    return thai_char_count(text) / len(text)


def _heuristic(text: str) -> int:
    thai = thai_char_count(text)
    other = len(text) - thai
    return max(1, int(thai * _TOKENS_PER_THAI_CHAR + other / _CHARS_PER_TOKEN_LATIN))


def estimate_tokens(text: str) -> int:
    """Estimate the number of tokens in *text*.

    Uses ``tiktoken`` when available for an accurate count, and falls back to a
    language-aware heuristic otherwise (Thai ~1 token/char, Latin ~4 chars/token).
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


def thai_needs_tiktoken(text: str, threshold: float = 0.10) -> bool:
    """True when the fallback heuristic would be unreliable for this text."""
    return not using_tiktoken() and thai_ratio(text) >= threshold
