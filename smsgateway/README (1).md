# SMS Gateway for Farmers (Hackathon Part 2)

Lets a farmer with a basic keypad phone text their **pincode + crop name**
(+ optional problem description) and get back AI-generated advice, in
their **local language**, as a single SMS (≤160 characters).

## How it works

```
Farmer's phone --SMS--> Twilio number --webhook POST--> Flask /sms
                                                             |
                                          1. parser.py: extract pincode + crop
                                          2. location_language.py: pincode -> state + language
                                          3. ai_advisor.py: ask Claude for short advice
                                          4. translator.py: translate to local language
                                          5. sms_utils.py: shrink to <=160 chars
                                                             |
Farmer's phone <--SMS-- Twilio <--TwiML reply-- Flask ------+
```

## Files

| File                    | Purpose                                                |
|-------------------------|---------------------------------------------------------|
| `app.py`                | Flask app + Twilio webhook (`/sms`)                     |
| `parser.py`             | Extracts pincode & crop name from raw SMS text          |
| `location_language.py`  | Maps Indian pincode -> state + local language code      |
| `ai_advisor.py`         | Calls Claude API for concise crop advice                |
| `translator.py`         | Translates English advice into the local language       |
| `sms_utils.py`          | Shrinks text to fit in one 160-char SMS                 |
| `requirements.txt`      | Python dependencies                                     |
| `.env.example`          | Template for required API keys                          |

## Setup (what YOU need to do)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a Twilio trial account + SMS-capable number**
   - Sign up at https://www.twilio.com/try-twilio (free trial works fine for a hackathon demo)
   - Buy/activate a phone number with SMS capability (Console > Phone Numbers > Buy a number)
   - Copy your **Account SID**, **Auth Token**, and the **phone number**

3. **Get an Anthropic API key**
   - https://console.anthropic.com > API Keys

4. **Configure secrets**
   ```bash
   cp .env.example .env
   ```
   Then fill in `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_PHONE_NUMBER`,
   and `ANTHROPIC_API_KEY` in `.env`.

5. **Run the server**
   ```bash
   python app.py
   ```
   It starts on `http://localhost:5000`.

6. **Expose it publicly with ngrok** (Twilio needs a public HTTPS URL to reach your laptop)
   ```bash
   ngrok http 5000
   ```
   Copy the `https://xxxx.ngrok-free.app` URL it gives you.

7. **Point Twilio at your webhook**
   - Twilio Console > Phone Numbers > Manage > Active Numbers > click your number
   - Under "Messaging Configuration" ("A message comes in"), set the webhook to:
     `https://xxxx.ngrok-free.app/sms` (method: HTTP POST)
   - Save.

8. **Test it**
   - Text your Twilio number from your own phone: `560001 tomato leaves turning yellow`
   - You should get back a short reply, translated into Kannada (since 560001 = Bengaluru/Karnataka)

## Testing without a real phone (curl)

Set `DISABLE_TWILIO_SIGNATURE_CHECK=true` in `.env` (already the default),
then simulate an incoming SMS:

```bash
curl -X POST http://localhost:5000/sms \
  -d "From=+919876543210" \
  -d "Body=560001 tomato leaves turning yellow"
```

You'll get back raw TwiML XML containing the reply text — that confirms
the whole pipeline (parse -> AI -> translate -> shrink) works end-to-end
before you even touch Twilio's dashboard.

**Important:** set `DISABLE_TWILIO_SIGNATURE_CHECK=false` before your real
demo/deployment if the webhook is reachable from the public internet —
otherwise anyone could POST fake messages to your `/sms` endpoint.

## Known limitations (be ready to mention these to judges)

- **Pincode -> language mapping is approximate.** It's based on India Post's
  2-digit PIN prefixes, which map to postal circles, not exact district
  boundaries. Good enough for a demo; a production version should use a
  proper pincode-to-district dataset.
- **`deep-translator`** uses the free Google Translate web endpoint — no API
  key needed (great for a hackathon) but it can rate-limit under heavy load.
  For production, swap in Google Cloud Translation API or India's own
  **Bhashini** API (built specifically for Indian languages).
- **Crop list is a fixed dictionary** (`parser.py`) with fuzzy matching for
  typos. Add more crops to `KNOWN_CROPS` as needed for your demo region.
- Twilio trial accounts can only text **verified** numbers — verify your
  own phone number in the Twilio Console before demoing, or upgrade the
  account.

## What's left for you to actually do

1. Get the Twilio + Anthropic API keys (step 2–3 above) — I can't create
   accounts on your behalf.
2. Run `pip install -r requirements.txt` in your own environment (this
   sandbox has no internet access to install/test the Twilio SDK live).
3. Set up ngrok (or deploy to a real host like Render/Railway/Fly.io)
   for a public URL Twilio can reach.
4. Wire the webhook URL into the Twilio console (step 7).
5. Optionally: connect this to your **Part 1** system if the AI advice
   should come from a shared backend/model rather than calling Claude
   directly — swap the internals of `get_crop_advice()` in `ai_advisor.py`.
