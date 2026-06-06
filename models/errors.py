"""
models/errors.py

Standardized error response models for consistent, accessible API error handling.
Every error response follows the same structure — making the API predictable
and easy to integrate for front-end developers and screen readers.

Accessibility:
  - error_code: machine-readable slug for programmatic handling
  - message: human-readable, localized explanation
  - detail: debugging context (hidden in production)
  - suggestion: actionable next step for the user
  - help_url: link to relevant documentation
  - locale: the language of the error message
"""

from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """
    Unified error response schema used across all endpoints.

    Accessibility:
      - error_code is a machine-readable slug (e.g. 'validation_error')
      - message is a human-readable, localized explanation
      - detail provides context for debugging (omitted in production)
      - suggestion offers actionable next steps
      - help_url points to relevant API documentation
      - locale indicates the language of the response
    """
    error_code: str = Field(
        ...,
        description="Machine-readable error identifier (e.g. 'validation_error', 'rate_limit_exceeded')",
    )
    message: str = Field(
        ...,
        description="Human-readable, localized error description",
    )
    detail: Optional[str] = Field(
        None,
        description="Additional context for debugging. Hidden in production environments.",
    )
    suggestion: Optional[str] = Field(
        None,
        description="Actionable suggestion to help the user resolve the error",
    )
    help_url: Optional[str] = Field(
        None,
        description="URL to API documentation or relevant help page (e.g. '/docs')",
    )

    model_config = {"json_schema_extra": {"examples": [
        {
            "error_code": "validation_error",
            "message": "Invalid mood score. Must be between 1 and 5.",
            "detail": "Field 'mood_score' received value 99",
            "suggestion": "Use a value from 1 (very low) to 5 (great).",
            "help_url": "/docs",
        },
        {
            "error_code": "rate_limit_exceeded",
            "message": "Too many requests. Please wait 30 seconds before trying again.",
            "detail": None,
            "suggestion": "Reduce request frequency or wait for the rate limit window to reset.",
            "help_url": "/docs",
        },
    ]}}
