"""
=====================================================================
 CROP ADVISOR — AI BRAIN (Logic Module)
=====================================================================
Isolated decision-maker. Talks directly to the Gemini API.
Takes weather/soil data + region -> returns a STRICT JSON object
with a Viability Score and an SMS-ready recommendation.

No chat, no markdown, no explanations outside the schema — just data.
=====================================================================
"""

import json
import google.generativeai as genai
from typing import TypedDict, Literal


# ---------------------------------------------------------------
# 0. CONFIG
# ---------------------------------------------------------------
# Set your key via env var: export GEMINI_API_KEY="..."
import os
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

MODEL_NAME = "gemini-2.0-flash"  # fast + cheap, good enough for structured scoring


# ---------------------------------------------------------------
# 1. GUARDRAILS — region-based hard rules
# ---------------------------------------------------------------
# These are enforced in TWO places for defense-in-depth:
#   (a) injected into the prompt so the model never even considers them
#   (b) checked again in Python after the response comes back,
#       in case the model hallucinates around the prompt rule.
#
# Extend this dict per state / district as you get real agri-dept data.
REGION_GUARDRAILS: dict[str, dict] = {
    "karnataka": {
        "banned_crops": ["sugarcane", "paddy"],  # example: water-stressed taluks
        "reason": "High water-table stress zone — water-intensive crops restricted "
                   "under local groundwater regulation.",
        "max_water_intensive_score": 40,  # cap viability score for thirsty crops
    },
    "maharashtra": {
        "banned_crops": ["sugarcane"],
        "reason": "Drought-prone district — sugarcane cultivation discouraged by "
                   "state agricultural advisory.",
        "max_water_intensive_score": 35,
    },
    "default": {
        "banned_crops": [],
        "reason": "",
        "max_water_intensive_score": 100,
    },
}

WATER_INTENSIVE_CROPS = {"sugarcane", "paddy", "banana", "rice"}


def get_guardrails(region: str) -> dict:
    return REGION_GUARDRAILS.get(region.strip().lower(), REGION_GUARDRAILS["default"])


# ---------------------------------------------------------------
# 2. OUTPUT SCHEMA — enforced via Gemini's structured output mode
# ---------------------------------------------------------------
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "crop": {"type": "string"},
        "viability_score": {
            "type": "integer",
            "description": "0-100. 0 = do not plant. 100 = ideal conditions.",
        },
        "risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "not_recommended"],
        },
        "reasoning": {
            "type": "string",
            "description": "One short sentence, max 25 words, farmer-facing.",
        },
        "sms_text": {
            "type": "string",
            "description": "Max 160 characters. Plain language. No jargon. "
                            "Must be directly sendable via SMS gateway.",
        },
        "guardrail_blocked": {
            "type": "boolean",
            "description": "True if this crop is blocked by local regulation.",
        },
    },
    "required": [
        "crop",
        "viability_score",
        "risk_level",
        "reasoning",
        "sms_text",
        "guardrail_blocked",
    ],
}


# ---------------------------------------------------------------
# 3. MASTER PROMPT
# ---------------------------------------------------------------
def build_system_prompt(region: str) -> str:
    gr = get_guardrails(region)
    banned = ", ".join(gr["banned_crops"]) if gr["banned_crops"] else "none"

    return f"""You are AgriBrain, a strict agronomic decision engine embedded in a
farmer advisory system. You are NOT a chatbot. You never produce conversational
text, greetings, apologies, or explanations outside the required JSON fields.

TASK
Given weather data, soil data, and a candidate crop, output a viability
assessment as JSON matching the provided schema exactly.

HARD RULES (violating any of these is a critical failure):
1. If the candidate crop appears in this region's banned list, you MUST set
   "guardrail_blocked": true, "viability_score": 0, "risk_level": "not_recommended",
   and the sms_text must clearly state the crop is restricted in this region and
   suggest the farmer ask about an alternative — do not suggest a specific
   replacement crop yourself in this message.
2. Region: {region}. Banned crops for this region: {banned}.
   Reason on file: {gr['reason'] or 'N/A'}.
3. Water-intensive crops ({', '.join(sorted(WATER_INTENSIVE_CROPS))}) can never
   score above {gr['max_water_intensive_score']} in this region, even if not
   formally banned, due to groundwater stress.
4. Never recommend a pesticide, fertilizer brand, or dosage. If asked to assess
   pest/disease risk, describe the risk only — do not prescribe treatment.
5. Never fabricate weather or soil numbers. Base the score only on the data
   given to you. If critical data is missing, lower the score and say so in
   "reasoning".
6. sms_text must be <= 160 characters, in plain farmer-facing language, no
   emojis, no technical jargon (e.g. say "soil is too wet" not "excess soil
   matric potential").
7. Output ONLY the JSON object. No markdown fences, no preamble, no commentary.

SCORING GUIDE (0-100 viability_score):
- 80-100: Conditions strongly favor this crop right now.
- 50-79: Workable but with meaningful risk (irrigation gap, marginal temp, etc).
- 20-49: Poor fit — significant risk of crop failure.
- 0-19: Do not plant / actively harmful given current data.
"""


def build_user_prompt(crop: str, weather: dict, soil: dict, region: str) -> str:
    return f"""CANDIDATE CROP: {crop}
REGION: {region}

WEATHER DATA:
{json.dumps(weather, indent=2)}

SOIL DATA:
{json.dumps(soil, indent=2)}

Assess viability now and return the JSON object per your instructions."""


# ---------------------------------------------------------------
# 4. TYPES
# ---------------------------------------------------------------
class WeatherInput(TypedDict, total=False):
    temp_c: float
    humidity_pct: float
    rainfall_mm_7day: float
    forecast_summary: str


class SoilInput(TypedDict, total=False):
    ph: float
    moisture_pct: float
    soil_type: str  # e.g. "loamy", "clay", "sandy"
    nitrogen_level: Literal["low", "medium", "high"]


class AdvisoryResult(TypedDict):
    crop: str
    viability_score: int
    risk_level: str
    reasoning: str
    sms_text: str
    guardrail_blocked: bool


# ---------------------------------------------------------------
# 5. THE BRAIN — main entry point
# ---------------------------------------------------------------
def get_crop_advisory(
    crop: str,
    weather: WeatherInput,
    soil: SoilInput,
    region: str,
) -> AdvisoryResult:
    """
    Calls Gemini with the master prompt + guardrails, gets back strict JSON,
    then re-validates the guardrail in Python (never trust the model alone).
    """
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        system_instruction=build_system_prompt(region),
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": RESPONSE_SCHEMA,
            "temperature": 0.2,  # low temp — this is a scoring task, not creative writing
        },
    )

    user_prompt = build_user_prompt(crop, weather, soil, region)
    response = model.generate_content(user_prompt)

    try:
        result: AdvisoryResult = json.loads(response.text)
    except (json.JSONDecodeError, AttributeError) as e:
        raise ValueError(f"Model did not return valid JSON: {e}\nRaw: {response.text}")

    # ---- Python-side guardrail re-check (defense in depth) ----
    gr = get_guardrails(region)
    if crop.strip().lower() in gr["banned_crops"]:
        result["guardrail_blocked"] = True
        result["viability_score"] = 0
        result["risk_level"] = "not_recommended"
        if "restricted" not in result["sms_text"].lower():
            result["sms_text"] = (
                f"{crop.title()} is restricted in your region due to local "
                f"farming rules. Ask us about alternative crops."
            )[:160]

    if crop.strip().lower() in WATER_INTENSIVE_CROPS:
        cap = gr["max_water_intensive_score"]
        if result["viability_score"] > cap:
            result["viability_score"] = cap

    # Hard length enforcement — never trust the model on this either
    if len(result["sms_text"]) > 160:
        result["sms_text"] = result["sms_text"][:157] + "..."

    return result


# ---------------------------------------------------------------
# 6. QUICK TEST
# ---------------------------------------------------------------
if __name__ == "__main__":
    demo_weather: WeatherInput = {
        "temp_c": 29.5,
        "humidity_pct": 68,
        "rainfall_mm_7day": 12,
        "forecast_summary": "Light showers expected over next 3 days",
    }
    demo_soil: SoilInput = {
        "ph": 6.2,
        "moisture_pct": 34,
        "soil_type": "loamy",
        "nitrogen_level": "medium",
    }

    result = get_crop_advisory(
        crop="sugarcane",
        weather=demo_weather,
        soil=demo_soil,
        region="Karnataka",
    )
    print(json.dumps(result, indent=2))
