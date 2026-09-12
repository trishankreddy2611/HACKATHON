"""
Translates English text into a local Indian language.

Uses deep-translator's GoogleTranslator, which does NOT require an API key
(great for a hackathon demo). For a production deployment, swap this out
for the paid Google Cloud Translation API or Bhashini (India's own
government translation API for Indian languages), which will be more
reliable and won't rate-limit you.
"""

from deep_translator import GoogleTranslator


def translate_text(text: str, target_lang: str) -> str:
    """
    Translates `text` (English) into `target_lang` (e.g. "hi", "ta", "te").
    Falls back to the original English text if translation fails for any
    reason (e.g. no internet, unsupported language code) -- we never want
    to fail to send an SMS just because translation broke.
    """
    if not text:
        return text

    if target_lang in ("en", None):
        return text

    try:
        translated = GoogleTranslator(source="en", target=target_lang).translate(text)
        return translated or text
    except Exception:
        # Fail safe: better to send English SMS than no SMS at all
        return text
