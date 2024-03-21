from common.log import logger
from bot.gemini.llm import genai
import time
import traceback


def clip_message(text):
    if len(text) <= 10:
        return text

    if is_chinese(text):
        return text[:10]
    else:
        return text[:10]
    
def is_chinese(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def trygen(model: genai.GenerativeModel, gemini_messages: list, max_retries = 2, delay = 1):
    for i in range(max_retries):
        try:
            return model.generate_content(gemini_messages)
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Exception occurred: {e}. Retrying...")
            time.sleep(delay)
    # raise Exception(f"Try generate content failed after {max_retries} retries.")