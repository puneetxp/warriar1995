"""
models/errors.py

Standardized error response models for consistent, accessible API error handling.
Every error response follows the same structure — making the API predictable
and easy to integrate for front-end developers and screen readers.
"""

from pydantic import BaseModel, Field
from typing import Optional


class ErrorResponse(BaseModel):
    """
    Unified error response schema used across all endpoints.

    Accessibility:
      - error_code is a machine-readable slug (e.g. 'validation_error')
      - message is a human-readable explanation
      - detail provides context for debugging
      - suggestion offers actionable next steps
    """
    error_code: str = Field(..., description="Machine-readable error identifier")
    message: str = Field(..., description="Human-readable error description")
    detail: Optional[str] = Field(None, description="Additional context for debugging")
    suggestion: Optional[str] = Field(None, description="Actionable suggestion to resolve the error")

    model_config = {"json_schema_extra": {"example": {
        "error_code": "validation_error",
        "message": "Invalid mood score. Must be between 1 and 5.",
        "detail": "Field 'mood_score' received value 99",
        "suggestion": "Use a value from 1 (very low) to 5 (great)."
    }}}
