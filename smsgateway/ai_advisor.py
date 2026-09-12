"""
Calls the Anthropic API to generate short, practical crop advice.

We explicitly instruct the model to answer in ~25 words or fewer, because:
  - it will later be translated (translation can expand length)
  - it will then be hard-truncated to 160 chars for the SMS
Getting the model to be concise up front avoids losing the most useful
information to truncation.
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"


def get_crop_advice(crop: str, state: str, farmer_message: str) -> str:
    """
    Returns a short English-language piece of farming advice.
    """
    prompt = (
        f"You are an agricultural extension officer advising a smallholder "
        f"farmer in {state}, India who grows {crop}.\n\n"
        f"Farmer's message (may include a problem description): \"{farmer_message}\"\n\n"
        "Give ONE practical, actionable piece of advice a farmer can act on "
        "today. Be extremely concise: 25 words maximum. No greetings, no "
        "disclaimers, no markdown. Plain, simple language a non-technical "
        "farmer can understand."
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=100,
        messages=[{"role": "user", "content": prompt}],
    )

    # Concatenate any text blocks in the response
    text_parts = [block.text for block in response.content if block.type == "text"]
    return " ".join(text_parts).strip()


def get_fallback_advice(crop: str) -> str:
    """Used if the API call fails, so the farmer still gets *something*."""
    if crop:
        return (
            f"Advice for {crop} is temporarily unavailable. Please try "
            f"again shortly or contact your local Krishi Vigyan Kendra."
        )
    return (
        "Sorry, we could not understand your message. Please reply with "
        "your PINCODE and CROP name, e.g. '560001 tomato leaves yellow'."
    )
