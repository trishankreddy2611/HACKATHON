"""
Parses a raw incoming SMS body into (pincode, crop_name).

Supports farmer messages like:
  "560001 tomato"
  "Tomato 560001"
  "My pincode is 560001 and crop is tomato, leaves turning yellow"
  "560001, cotton, pests eating leaves"

Strategy:
  1. Pincode: find any standalone 6-digit number (Indian PIN codes are always 6 digits).
  2. Crop: fuzzy-match words in the message against a known crop dictionary
     (so "tomatoes", "TOMATO", "tomatoe" typos still map to "tomato").
"""

import re
import difflib

PINCODE_REGEX = re.compile(r"\b(\d{6})\b")

# Known crop names (extend this list as needed for your hackathon demo)
KNOWN_CROPS = [
    "rice", "wheat", "maize", "cotton", "sugarcane", "soybean", "groundnut",
    "tomato", "potato", "onion", "chilli", "chili", "brinjal", "okra",
    "banana", "mango", "grapes", "cabbage", "cauliflower", "mustard",
    "gram", "bajra", "jowar", "millet", "turmeric", "ginger", "garlic",
    "tea", "coffee", "coconut", "jute", "barley", "sunflower", "sesame",
]


def extract_pincode(text: str):
    match = PINCODE_REGEX.search(text)
    return match.group(1) if match else None


def extract_crop(text: str):
    """
    Tokenize the message, strip punctuation/digits, and fuzzy-match each
    word against KNOWN_CROPS. Returns the best match above a similarity
    threshold, or None if nothing looks like a crop name.
    """
    words = re.findall(r"[A-Za-z]+", text.lower())

    best_crop = None
    best_score = 0.0

    for word in words:
        if len(word) < 3:
            continue
        matches = difflib.get_close_matches(word, KNOWN_CROPS, n=1, cutoff=0.75)
        if matches:
            # exact match wins immediately
            if matches[0] == word:
                return matches[0]
            score = difflib.SequenceMatcher(None, word, matches[0]).ratio()
            if score > best_score:
                best_score = score
                best_crop = matches[0]

    return best_crop


def parse_message(text: str):
    """
    Returns a dict: {"pincode": str|None, "crop": str|None, "raw": text}
    """
    pincode = extract_pincode(text)
    crop = extract_crop(text)
    return {"pincode": pincode, "crop": crop, "raw": text.strip()}
