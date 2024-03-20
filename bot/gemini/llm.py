import google.generativeai as genai
from google.generativeai.types.safety_types import HarmCategory, HarmBlockThreshold
from config import conf
import random


# Disable all safety filters
SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

keys = conf().get("gemini_api_key")
keys = keys.split("|")
keys = [key.strip() for key in keys]
if not keys:
    raise Exception("Please set a valid API key in Config!")
genai.configure(api_key=random.choice(keys))


model = genai.GenerativeModel("gemini-pro", safety_settings=SAFETY_SETTINGS)
img_model = genai.GenerativeModel("gemini-pro-vision", safety_settings=SAFETY_SETTINGS)
