"""
Maps an Indian PIN code to a state and a local language code
(used later for translating the AI's advice with deep-translator,
which uses Google Translate language codes: hi, mr, pa, gu, ta, te,
kn, ml, bn, or, en, etc.)

India Post PIN codes are structured as:
  1st digit  -> Postal region (1 of 9 zones)
  1st+2nd    -> Postal circle / sub-region (roughly maps to a state or state-cluster)

This is an approximation good enough for a hackathon demo. It is NOT
survey-grade accurate (a few districts near state borders will be off),
but it covers the major agricultural states correctly.
"""

# Two-digit PIN prefix -> (state name, ISO-ish language code for deep-translator)
PREFIX_MAP = {
    # Delhi / Haryana / Punjab / HP / J&K / Chandigarh (zone 1)
    "11": ("Delhi", "hi"),
    "12": ("Haryana", "hi"),
    "13": ("Punjab", "pa"),
    "14": ("Punjab", "pa"),
    "15": ("Punjab", "pa"),
    "16": ("Chandigarh", "hi"),
    "17": ("Himachal Pradesh", "hi"),
    "18": ("Jammu & Kashmir", "ur"),
    "19": ("Jammu & Kashmir", "ur"),

    # Uttar Pradesh / Uttarakhand (zone 2)
    "20": ("Uttar Pradesh", "hi"),
    "21": ("Uttar Pradesh", "hi"),
    "22": ("Uttar Pradesh", "hi"),
    "23": ("Uttar Pradesh", "hi"),
    "24": ("Uttar Pradesh", "hi"),
    "25": ("Uttarakhand", "hi"),
    "26": ("Uttarakhand", "hi"),
    "27": ("Uttar Pradesh", "hi"),
    "28": ("Uttar Pradesh", "hi"),

    # Rajasthan (zone 3)
    "30": ("Rajasthan", "hi"),
    "31": ("Rajasthan", "hi"),
    "32": ("Rajasthan", "hi"),
    "33": ("Rajasthan", "hi"),
    "34": ("Rajasthan", "hi"),

    # Gujarat / Daman & Diu / Dadra Nagar Haveli (zone 3 contd.)
    "36": ("Gujarat", "gu"),
    "37": ("Gujarat", "gu"),
    "38": ("Gujarat", "gu"),
    "39": ("Gujarat", "gu"),

    # Maharashtra / Goa (zone 4)
    "40": ("Maharashtra", "mr"),
    "41": ("Maharashtra", "mr"),
    "42": ("Maharashtra", "mr"),
    "43": ("Maharashtra", "mr"),
    "44": ("Maharashtra", "mr"),
    "45": ("Madhya Pradesh", "hi"),
    "46": ("Madhya Pradesh", "hi"),
    "47": ("Madhya Pradesh", "hi"),
    "48": ("Madhya Pradesh", "hi"),

    # Andhra Pradesh / Telangana / Karnataka (zone 5)
    "50": ("Telangana", "te"),
    "51": ("Andhra Pradesh", "te"),
    "52": ("Andhra Pradesh", "te"),
    "53": ("Andhra Pradesh", "te"),
    "56": ("Karnataka", "kn"),
    "57": ("Karnataka", "kn"),
    "58": ("Karnataka", "kn"),
    "59": ("Karnataka", "kn"),

    # Tamil Nadu / Kerala / Puducherry (zone 6)
    "60": ("Tamil Nadu", "ta"),
    "61": ("Tamil Nadu", "ta"),
    "62": ("Tamil Nadu", "ta"),
    "63": ("Tamil Nadu", "ta"),
    "64": ("Tamil Nadu", "ta"),
    "67": ("Kerala", "ml"),
    "68": ("Kerala", "ml"),
    "69": ("Kerala", "ml"),

    # West Bengal / Odisha / NE states (zone 7)
    "70": ("West Bengal", "bn"),
    "71": ("West Bengal", "bn"),
    "72": ("West Bengal", "bn"),
    "73": ("West Bengal", "bn"),
    "75": ("Odisha", "or"),
    "76": ("Odisha", "or"),
    "77": ("Odisha", "or"),
    "78": ("Assam", "as"),
    "79": ("Northeastern States", "as"),

    # Bihar / Jharkhand (zone 8)
    "80": ("Bihar", "hi"),
    "81": ("Bihar", "hi"),
    "82": ("Jharkhand", "hi"),
    "83": ("Jharkhand", "hi"),
    "84": ("Bihar", "hi"),
    "85": ("Bihar", "hi"),
}

DEFAULT_STATE = "India"
DEFAULT_LANGUAGE = "hi"  # Hindi fallback if prefix isn't found


def get_state_and_language(pincode: str):
    """
    Given a 6-digit Indian pincode string, return (state_name, language_code).
    Falls back to (DEFAULT_STATE, DEFAULT_LANGUAGE) if unrecognized.
    """
    if not pincode or len(pincode) < 2:
        return DEFAULT_STATE, DEFAULT_LANGUAGE

    prefix = pincode[:2]
    return PREFIX_MAP.get(prefix, (DEFAULT_STATE, DEFAULT_LANGUAGE))
