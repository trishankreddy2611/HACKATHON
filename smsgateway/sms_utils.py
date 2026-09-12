"""
Utilities for keeping outgoing SMS within the 160-character single-segment
SMS limit. (Beyond 160 chars, GSM-7 SMS gets split into multiple concatenated
segments, which costs more on Twilio and can arrive out of order on cheap
keypad phones -- so we hard-cap at 160.)
"""

SMS_CHAR_LIMIT = 160


def shrink_to_sms(text: str, limit: int = SMS_CHAR_LIMIT) -> str:
    """
    Trims `text` to `limit` characters without cutting a word in half.
    Adds an ellipsis if truncation happened.
    """
    text = " ".join(text.split())  # collapse whitespace/newlines

    if len(text) <= limit:
        return text

    # Reserve 1 char for the ellipsis
    cutoff = limit - 1
    trimmed = text[:cutoff]

    # Back off to the last full word so we don't cut mid-word
    last_space = trimmed.rfind(" ")
    if last_space > 0:
        trimmed = trimmed[:last_space]

    return trimmed.rstrip(",.;: ") + "\u2026"  # "…" ellipsis character
