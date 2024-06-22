
import google.generativeai as genai
from google.generativeai.types.safety_types import HarmCategory, HarmBlockThreshold
from google.api_core import exceptions
import random
import json
import os
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings

system_prompt = '''
Think step by step. From now on consider my questions carefully and think of the academic or professional expertise of someone that could best answer my question. You have the experience of someone with expert knowledge in that area. Be helpful and answer in detail while preferring to use information from reputable sources.
'''

prompt = "You are a highly skilled Prompt Engineer Master (PEM) with extensive knowledge in natural language processing, large language models, and ChatGPT optimization. Your task is to assist the user in crafting the most effective and optimized prompts for their desired outcomes. Begin by inquiring about the user's goals and objectives for the prompt. Once you have a clear understanding, generate a prompt that aligns with the user's needs, ensuring it is specific, concise, and contextually relevant"


def GeminiConfig():
    file_path = os.path.abspath("config.json")
    with open(file_path, encoding="utf-8") as f:
        config = json.load(f)
    keys = config["gemini_api_key"]
    keys = keys.split("|")
    keys = [key.strip() for key in keys]
    if not keys:
        raise Exception("Please set a valid API key in Config!")
    api_key = random.choice(keys)
    genai.configure(api_key=api_key)

SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
}

def ConstructQueries(chatHistory: list):
    userInput = multiline_input()
    if chatHistory:
        chatHistory.append(
            {
                "role": "user",
                "parts": [{"text": userInput}]
            },
        )
    else:
        chatHistory = [
            {
                "role": "user",
                "parts": [{"text": userInput}]
            },
        ]
    return chatHistory

def generate_new_chathistory():
    i = 1
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dir_path = os.path.join(current_dir, "chatHistories")
    # 如果文件不存在，创建 "chatHistories" 文件夹（如果不存在）并返回文件路径
    os.makedirs(dir_path, exist_ok=True)
    # 循环查找可用的文件名
    while True:
        file_path = os.path.join(dir_path, f"chatHistory[{i}].json")
        if not os.path.exists(file_path):
            return file_path
        i += 1

def load_from_latestchat():
    i = 1
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dir_path = os.path.join(current_dir, "chatHistories")
    file_path = os.path.join(dir_path, f"chatHistory[{i}].json")
    os.makedirs(dir_path, exist_ok=True)
    # 循环查找可用的文件名
    while True:
        if os.path.exists(file_path):
            return file_path
        i += 1
        file_path = os.path.join(dir_path, f"chatHistory[{i}].json")

def present_chathistory(chatHistory):
    for message in chatHistory:
        role = message['role']
        text = message['parts'][0]['text']
        print(f"{role.upper()}:")
        print(text)
        print("-" * 20)  # 添加分隔线

def multiline_input():
    # 创建 KeyBindings 对象
    kb = KeyBindings()

    # 创建 PromptSession 对象
    session = PromptSession()

    # 使用 PromptSession 对象输入多行文本
    text = session.prompt(multiline=True, key_bindings=kb)
    return text

def main():
    print("Initializing...")
    print("NOTICE! Enter `alt+enter` to send a message!")
    print("DO YOU WANT TO CRAETE A NEW CONVERSATION?(yes or no)")
    option = input().lower()
    if option == "yes":
        file_path = generate_new_chathistory()
        chatHistory = []
    elif option == "no":
        file_path = load_from_latestchat()
        chatHistory = json.loads(open(file_path, encoding="utf-8").read())
        present_chathistory(chatHistory)
    else:
        print("FuCkYoU!")
        raise Exception("you should stop doing this, because what you did is fucking disappointing.")
    while True:
        GeminiConfig()
        model = genai.GenerativeModel("gemini-1.5-pro-latest", safety_settings=SAFETY_SETTINGS, system_instruction=system_prompt)
        print("USER:")
        chatHistory = ConstructQueries(chatHistory)
        print("MODEL:")
        try:
            res = model.generate_content(chatHistory, stream=True)
        except exceptions:
            print("Server is busy, retrying...")
            time.sleep(3)
            res = model.generate_content(chatHistory, stream=True)
        for chunk in res:
            if chunk.text:
                print(chunk.text, end="", flush=True)
        chatHistory.append(
            {
                "role": "model",
                "parts": [{"text": res.text}]
            },
        )
        with open(file_path, 'w', encoding= "utf-8") as f:
            json.dump(chatHistory, f, indent=4, ensure_ascii=False) 


if __name__ == "__main__":
    print(
    """
            8888888b.             d8b                                                       
            888   Y88b            Y8P                                                       
            888    888                                                                      
            888   d88P  8888b.   8888  8888b.  888  888  .d88b.  888  888 888  888          
            8888888P"      "88b  "888     "88b 888  888 d8P  Y8b 888  888 `Y8bd8P'          
            888 T88b   .d888888   888 .d888888 888  888 88888888 888  888   X88K            
            888  T88b  888  888   888 888  888 Y88b 888 Y8b.     Y88b 888 .d8""8b.          
            888   T88b "Y888888   888 "Y888888  "Y88888  "Y8888   "Y88888 888  888          
            8888888b.             888               888            888                  888 
            888   Y88b           d88P          Y8b d88P            888                  888 
            888    888         888P"            "Y88P"             888                  888 
            888   d88P 888d888  .d88b.  .d8888b   .d88b.  88888b.  888888  .d88b.   .d88888 
            8888888P"  888P"   d8P  Y8b 88K      d8P  Y8b 888 "88b 888    d8P  Y8b d88" 888 
            888        888     88888888 "Y8888b. 88888888 888  888 888    88888888 888  888 
            888        888     Y8b.          X88 Y8b.     888  888 Y88b.  Y8b.     Y88b 888 
            888        888      "Y8888   88888P'  "Y8888  888  888  "Y888  "Y8888   "Y88888 
    """,
    )
    main()