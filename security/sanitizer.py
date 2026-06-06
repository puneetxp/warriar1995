"""
utils/sanitizer.py

Input sanitization to prevent prompt injection and XSS.
All free-text user inputs pass through sanitize_text() before
being interpolated into LLM prompts.
"""

import re
import html
from typing import Optional


# Characters that could break out of a prompt template
_PROMPT_INJECTION_PATTERN = re.compile(
    r"(ignore\s+(previous|all|above)\s+instructions?|"
    r"system\s*prompt|jailbreak|forget\s+everything|"
    r"<\s*/?s(ystem|cript)[^>]*>|"
    r"\{\{.*?\}\}|"          # template literals
    r"\$\{.*?\})",            # JS-style interpolation
    re.IGNORECASE | re.DOTALL,
)

# Strip HTML tags
_HTML_TAG_PATTERN = re.compile(r"<[^>]+>")

# Collapse excessive whitespace
_WHITESPACE_PATTERN = re.compile(r"\s{3,}")


def sanitize_text(
    text: str,
    max_length: Optional[int] = None,
    allow_newlines: bool = True,
) -> str:
    """
    Sanitize free-text user input before embedding in LLM prompts.

    Steps:
    1. HTML-escape special characters
    2. Strip HTML tags
    3. Remove prompt-injection patterns
    4. Collapse excessive whitespace
    5. Truncate to max_length

    Args:
        text: Raw user input string
        max_length: Hard truncation limit (characters)
        allow_newlines: Whether to preserve newlines

    Returns:
        Sanitized string safe for LLM prompt interpolation
    """
    if not isinstance(text, str):
        return ""

    # 1. Escape HTML entities
    cleaned = html.escape(text, quote=True)

    # 2. Strip any residual HTML tags
    cleaned = _HTML_TAG_PATTERN.sub("", cleaned)

    # 3. Remove prompt-injection attempts
    cleaned = _PROMPT_INJECTION_PATTERN.sub("[removed]", cleaned)

    # 4. Normalise whitespace
    if not allow_newlines:
        cleaned = cleaned.replace("\n", " ").replace("\r", " ")
    cleaned = _WHITESPACE_PATTERN.sub("  ", cleaned).strip()

    # 5. Enforce length cap
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip() + "…"

    return cleaned


def sanitize_list(items: list, max_items: int = 10, max_item_length: int = 50) -> list:
    """Sanitize a list of short strings (e.g. emotion tags)."""
    return [
        sanitize_text(str(item), max_length=max_item_length, allow_newlines=False)
        for item in items[:max_items]
        if item
    ]


def mask_student_id(student_id: str) -> str:
    """Return a safe display version of student_id for logs (never log raw IDs in prod)."""
    if len(student_id) <= 4:
        return "***"
    return student_id[:2] + "*" * (len(student_id) - 4) + student_id[-2:]
