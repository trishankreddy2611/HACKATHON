"""
SMS Gateway for farmers - Twilio webhook.

Flow for every incoming text:
  1. Twilio POSTs the incoming SMS to /sms
  2. parser.py extracts pincode + crop name from the raw text
  3. location_language.py maps pincode -> state + local language
  4. ai_advisor.py asks Claude for short, practical advice
  5. translator.py translates that advice into the farmer's local language
  6. sms_utils.py shrinks the final text to <=160 characters
  7. We reply via TwiML so Twilio sends it back as an SMS

Run locally:
  pip install -r requirements.txt
  cp .env.example .env   # then fill in real keys
  python app.py

Expose to Twilio during dev (Twilio needs a public URL):
  ngrok http 5000
  -> copy the https ngrok URL, set it (with /sms appended) as the
     "A MESSAGE COMES IN" webhook on your Twilio phone number, in the
     Twilio Console > Phone Numbers > Manage > Active Numbers.
"""

import os
import logging
from flask import Flask, request, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from dotenv import load_dotenv

from parser import parse_message
from location_language import get_state_and_language
from ai_advisor import get_crop_advice, get_fallback_advice
from translator import translate_text
from sms_utils import shrink_to_sms

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sms_gateway")

TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
DISABLE_SIG_CHECK = os.environ.get("DISABLE_TWILIO_SIGNATURE_CHECK", "false").lower() == "true"


def is_valid_twilio_request(req) -> bool:
    """
    Verifies the request really came from Twilio (prevents anyone from
    spoofing POSTs to your webhook). Skipped only when explicitly disabled
    for local curl-based testing.
    """
    if DISABLE_SIG_CHECK:
        return True

    validator = RequestValidator(TWILIO_AUTH_TOKEN)
    signature = req.headers.get("X-Twilio-Signature", "")
    url = req.url
    return validator.validate(url, req.form, signature)


@app.route("/sms", methods=["POST"])
def sms_webhook():
    if not is_valid_twilio_request(request):
        abort(403)

    incoming_text = request.form.get("Body", "")
    from_number = request.form.get("From", "unknown")
    log.info("Incoming SMS from %s: %r", from_number, incoming_text)

    parsed = parse_message(incoming_text)
    pincode, crop = parsed["pincode"], parsed["crop"]

    resp = MessagingResponse()

    if not pincode or not crop:
        # Ask the farmer to resend in the right format instead of guessing
        reply_text = (
            "Please send: PINCODE CROP e.g. '560001 tomato'. "
            "You can also describe the problem."
        )
        resp.message(shrink_to_sms(reply_text))
        return str(resp)

    state, lang = get_state_and_language(pincode)

    try:
        advice_en = get_crop_advice(crop=crop, state=state, farmer_message=incoming_text)
    except Exception as e:
        log.exception("AI advisor failed: %s", e)
        advice_en = get_fallback_advice(crop)

    advice_local = translate_text(advice_en, lang)
    final_sms = shrink_to_sms(advice_local)

    log.info("Replying to %s (lang=%s): %r", from_number, lang, final_sms)
    resp.message(final_sms)
    return str(resp)


@app.route("/", methods=["GET"])
def health_check():
    return "SMS Gateway is running.", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
