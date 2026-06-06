"""
utils/i18n.py

Lightweight internationalization (i18n) module for the Mental Wellness Tracker.

Supports English (en) and Hindi (hi) — the two primary languages for Indian
competitive exam students. Designed for accessibility compliance.

Usage:
    from utils.i18n import get_locale, t
    locale = get_locale(request)
    message = t("safety_message_default", locale)
"""

from typing import Optional
from fastapi import Request


# ── Supported locales ──────────────────────────────────────────────────────────

SUPPORTED_LOCALES = {"en", "hi"}
DEFAULT_LOCALE = "en"


# ── Translation dictionary ────────────────────────────────────────────────────

_TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Error messages ─────────────────────────────────────────────────────
    "error.validation": {
        "en": "Invalid input in field '{field}': {detail}",
        "hi": "फ़ील्ड '{field}' में अमान्य इनपुट: {detail}",
    },
    "error.validation_suggestion": {
        "en": "Check the API docs at /docs for the correct request format.",
        "hi": "सही अनुरोध प्रारूप के लिए /docs पर API दस्तावेज़ देखें।",
    },
    "error.internal": {
        "en": "An unexpected error occurred. Please try again later.",
        "hi": "एक अप्रत्याशित त्रुटि हुई। कृपया बाद में पुनः प्रयास करें।",
    },
    "error.internal_suggestion": {
        "en": "If this persists, contact support.",
        "hi": "यदि यह समस्या बनी रहती है, तो सहायता से संपर्क करें।",
    },
    "error.rate_limit": {
        "en": "Too many requests. Please wait {seconds} seconds before trying again.",
        "hi": "बहुत सारे अनुरोध। कृपया पुनः प्रयास करने से पहले {seconds} सेकंड प्रतीक्षा करें।",
    },
    "error.rate_limit_suggestion": {
        "en": "Reduce request frequency or wait for the rate limit window to reset.",
        "hi": "अनुरोध की आवृत्ति कम करें या दर सीमा विंडो रीसेट होने की प्रतीक्षा करें।",
    },
    "error.agent_failed": {
        "en": "AI analysis could not be completed. Please try again.",
        "hi": "AI विश्लेषण पूरा नहीं हो सका। कृपया पुनः प्रयास करें।",
    },

    # ── Crisis / safety messages ───────────────────────────────────────────
    "crisis.safety_default": {
        "en": "You matter. Your worth is not defined by your exam results.",
        "hi": "आप मायने रखते हैं। आपकी कीमत आपके परीक्षा परिणामों से तय नहीं होती।",
    },
    "crisis.immediate_action_high": {
        "en": (
            "⚠️ Please reach out to a trusted adult, parent, teacher, or mental health "
            "professional immediately. Call a helpline now — you don't have to face this alone."
        ),
        "hi": (
            "⚠️ कृपया तुरंत किसी विश्वसनीय बड़े, माता-पिता, शिक्षक, या मानसिक स्वास्थ्य "
            "विशेषज्ञ से संपर्क करें। अभी हेल्पलाइन पर कॉल करें — आपको अकेले इसका सामना नहीं करना है।"
        ),
    },
    "crisis.immediate_action_low": {
        "en": "Take a short break and breathe deeply.",
        "hi": "थोड़ा ब्रेक लें और गहरी साँस लें।",
    },
    "crisis.safety_checkin": {
        "en": "You matter. Exams are just a step, not your entire worth.",
        "hi": "आप मायने रखते हैं। परीक्षा बस एक कदम है, आपकी पूरी कीमत नहीं।",
    },

    # ── Mood labels ────────────────────────────────────────────────────────
    "mood.unknown": {
        "en": "Unknown",
        "hi": "अज्ञात",
    },

    # ── Wellness ───────────────────────────────────────────────────────────
    "wellness.no_message": {
        "en": "Our wellness coach is here to help you.",
        "hi": "हमारा वेलनेस कोच आपकी मदद के लिए यहाँ है।",
    },

    # ── General API ────────────────────────────────────────────────────────
    "api.not_ready": {
        "en": "Service is not ready. API key is not configured.",
        "hi": "सेवा तैयार नहीं है। API कुंजी कॉन्फ़िगर नहीं है।",
    },
}


# ── Public API ─────────────────────────────────────────────────────────────────

def get_locale(request: Request) -> str:
    """
    Extract the preferred locale from the Accept-Language header.

    Parses the header and returns the first supported locale found.
    Falls back to 'en' if no supported locale is detected.

    Args:
        request: The incoming FastAPI request.

    Returns:
        A locale string, e.g. 'en' or 'hi'.
    """
    accept = request.headers.get("accept-language", "")
    # Parse "hi-IN,hi;q=0.9,en-US;q=0.8,en;q=0.7" style headers
    for part in accept.split(","):
        lang = part.split(";")[0].strip().lower()
        # Check exact match first, then language prefix
        if lang in SUPPORTED_LOCALES:
            return lang
        prefix = lang.split("-")[0]
        if prefix in SUPPORTED_LOCALES:
            return prefix
    return DEFAULT_LOCALE


def t(key: str, locale: str = DEFAULT_LOCALE, **kwargs: str) -> str:
    """
    Translate a key into the given locale.

    Supports placeholder substitution via keyword arguments.
    Falls back to English if the key or locale is not found.

    Args:
        key:    Translation key, e.g. 'crisis.safety_default'
        locale: Target locale, e.g. 'hi'
        **kwargs: Placeholder values for string formatting

    Returns:
        The translated (and formatted) string.

    Examples:
        >>> t("error.rate_limit", "hi", seconds="30")
        'बहुत सारे अनुरोध। कृपया पुनः प्रयास करने से पहले 30 सेकंड प्रतीक्षा करें।'
    """
    translations = _TRANSLATIONS.get(key, {})
    text = translations.get(locale) or translations.get(DEFAULT_LOCALE, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, IndexError):
            pass  # Return unformatted if placeholders don't match
    return text


def get_supported_locales() -> list[str]:
    """Return a sorted list of supported locale codes."""
    return sorted(SUPPORTED_LOCALES)
