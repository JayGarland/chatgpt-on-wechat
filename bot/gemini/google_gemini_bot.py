"""
Google gemini bot

@author zhayujie + rajayoux
@Date 2023/12/15 + 3/20/2024
"""
# encoding:utf-8

from bot.bot import Bot
from bot.gemini.google_gemini_sessionmanager import GeminiSessionManager, GeminiSession
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.gemini.utils import *
from PIL import Image
from common import memory
import io
import time
import traceback
from google.generativeai.types.safety_types import HarmCategory, HarmBlockThreshold
import google.generativeai as genai
import random



# TODO add multi patterns talk when with a pic, and by using file API
# TODO fix environment abnormal in web fetch
class GoogleGeminiBot(Bot):
    SAFETY_SETTINGS = {
        'HATE': 'BLOCK_NONE',
        'HARASSMENT': 'BLOCK_NONE',
        'SEXUAL' : 'BLOCK_NONE',
        'DANGEROUS' : 'BLOCK_NONE'
    }
    GENERATION_CONFIG = {
        "temperature": 1.6,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }
    def __init__(self):
        super().__init__()
        self.sessions = GeminiSessionManager(GeminiSession, model=conf().get("model"))
        self.bot_statement = str("")

    def reply(self, query: str, context: Context = None) -> Reply:
        GoogleGeminiBot.GeminiApiConfig()
        user_data = conf().get_user_data(context["receiver"])
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]


            #web fetch
            webPagecache = memory.USER_WEBPAGE_CACHE.get(session_id)
            if webPagecache:
                query = f"\n[user](#webpage_context)\n{webPagecache}\n\n\n" + query 
                logger.debug(memory.USER_WEBPAGE_CACHE)
                del memory.USER_WEBPAGE_CACHE[session_id]
            
            #file fetch
            fileCache = memory.USER_FILE_CACHE.get(session_id)
            # logger.debug(fileCache)
            if fileCache:
                fileinfo = self.process_file_msg(session_id, fileCache)
                if fileinfo:
                    if f"\U0001F605" in fileinfo:
                        return fileinfo
                    else:
                        query = fileinfo + "\n\n[user](#message)\n" + query

            session = self.sessions.session_query(query, session_id)
            # logger.info(session.messages)
            
            # session = self.sessions.session_query(query, session_id)
            # logger.debug(session.messages[-1]['content'])
            
            #construct gemini_messages
            system_prompt, pre_reply = self.init_prompt_botstatement(context, session)
            model = genai.GenerativeModel("gemini-1.5-flash-latest", safety_settings=GoogleGeminiBot.SAFETY_SETTINGS, system_instruction=system_prompt, generation_config=GoogleGeminiBot.GENERATION_CONFIG)
            gemini_messages = self._convert_to_gemini_messages(GoogleGeminiBot.filter_messages(session.messages))
            logger.info(gemini_messages)
            
            # reply generate process
            img_cache = memory.USER_IMAGE_CACHE.get(session_id)
            if img_cache:
                img = self.process_img(session_id, img_cache)
                system_prompt, noused_prereply = self.init_prompt_botstatement(context, session)
                img_model = model
                gemini_messages_img = [query, img]
                if context["stream"]:
                    response = self.stream_reply(gemini_messages_img, context, img_model)
                else:
                    response = img_model.generate_content(gemini_messages_img) #when use the vision no persona
                reply_text = response.text
            else:
                try:
                    if context["stream"]:
                        response = self.stream_reply(gemini_messages, context, model)
                    else:
                        response = model.generate_content(gemini_messages)
                    reply_text = response.text[:-2]
                except Exception as e:
                    traceback.print_exc()
                    logger.error(f"Exception occurred: {e}！")
                    # context.get("channel").send(Reply(ReplyType.TEXT, f"服务器繁忙，请重试!"), context)
                    return Reply(ReplyType.INFO, f"服务器繁忙\n请尝试再问我一次 \U0001F64F \n```\n{e}\n```")
                    # time.sleep(1)
            # logger.debug(response)
            

            #append reply msg to session
            logger.info(f"[Gemini] reply={reply_text}")
            self.sessions.session_reply(reply_text, session_id)
            
            #decorate and format text
            reply_text = reply_text.replace("**", "#")

            #Critical
            if context["stream"]:
                reply_text = ""

            #botStatement
            if self.bot_statement:
                if context["isgroup"] and not context["stream"] and not context["voice"]:
                    reply_text += "\n\n" + self.bot_statement
                else:
                    reply_text += self.bot_statement
            #return reply
            if len(session.messages) == 3 and not context["voice"]:
                return self.wrap_promo_msg(context, reply_text)
            return Reply(ReplyType.TEXT, reply_text)
        except Exception as e:
            traceback.print_exc()
            logger.error("[Gemini] fetch reply error, may contain unsafe content")
            logger.error(e)
            return Reply(ReplyType.INFO, f"我脑壳短路了一下，Sorry！\U0001F64F \n\nDebug Info:\n{e}")

    def _convert_to_gemini_messages(self, messages: list):
        res = []
        for msg in messages:
            if msg.get("role") == "user":
                role = "user"
            elif msg.get("role") == "assistant":
                role = "model"
            else:
                continue
            res.append({
                "role": role,
                "parts": [{"text": msg.get("content")}]
            })
        return res

    @staticmethod
    def filter_messages(messages: list):
        res = []
        turn = "user"
        if not messages:
            return res
        for i in range(len(messages) - 1, -1, -1):
            message = messages[i]
            if message.get("role") != turn:
                continue
            res.insert(0, message)
            if turn == "user":
                turn = "assistant"
            elif turn == "assistant":
                turn = "user"
        return res

    def construct_preset(self, context):
        persona, pre_reply = self.init_prompt_botstatement(context)
        res = []
        res.append({
                "role": "user",
                "parts": [{"text": persona}]
            })
        res.append({
                "role": "model",
                "parts": [{"text": pre_reply}]
            })
        # logger.info(res)
        return res
    
    def init_prompt_botstatement(self, context, session):#FIXME replace the current solution for loading config from config.json since the json format doesn't support multi lines breaking, so that I have convert from the multi to single line by using https://simpleinternettool.com/replace-line-breaks-with-n/
        persona = None
        pre_reply = None
        
        for setting_pairs in conf().get("customerSet"):##TODO fix the Repeat same speech pattern as the last convo problem
            for key, cusprompt in dict(setting_pairs).items():
                if key == context["session_id"]:
                    persona = cusprompt
                    pre_reply = setting_pairs["pre_reply"]
                    self.bot_statement = setting_pairs["botstatement"]
                    conf().__setitem__("voicespecies", "zh-CN-YunyangNeural")
                    break
        if not persona:
            persona = session.system_prompt
            pre_reply = conf().get("pre_reply")
            self.bot_statement = conf().get("sydney_statement")
            conf().__setitem__("voicespecies", "zh-CN-XiaoxiaoNeural") #zh-CN-XiaoxiaoNeural optional, more matual
        if not context["isgroup"]:
            self.bot_statement = ""
        return persona, pre_reply
    
    def wrap_promo_msg(self, context, reply_text):
        credit = conf().get("sydney_credit") 
        reply_text += "\n\n" + str(credit).format(mode = f"语音: {context['voice']}\n流式输出: {context['stream']}\n已读通知: {context['readfb']}")
        try:
            qridimg = open('.\wechatID.jpg', 'rb')
        except:
            qridimg = None
        try:
            context.get("channel").send(Reply(ReplyType.TEXT, reply_text), context)
            return Reply(ReplyType.IMAGE, qridimg)
        except Exception as e:
            logger.warning(e)
            context.get("channel").send(Reply(ReplyType.TEXT, reply_text), context)
            return Reply(ReplyType.IMAGE, qridimg)
    
    def process_img(self, session_id, img_cache):
        try:
            msg = img_cache.get("msg")
            path = img_cache.get("path")
            msg.prepare()
            logger.info(f"[SYDNEY] query with images, path={path}")
            '''
                img = genai.upload_file(path, mime_type= "application/octet-stream")
            '''
            with open(path, "rb") as f:
                img_bytes = f.read()
            img = Image.open(io.BytesIO(img_bytes))
            memory.USER_IMAGE_CACHE[session_id] = None
            return img
        except Exception as e:
            logger.exception(e)

    def process_file_msg(self, session_id, file_cache):
        try:
            msg = file_cache.get("msg")
            path = file_cache.get("path")
            msg.prepare()
            logger.info(f"[Gemini] query with files, path={path}")              
            messages = asyncio.run(build_docx_msg(path))
            del memory.USER_FILE_CACHE[session_id]
            return messages
        except Exception as e:
            logger.exception(e)

    def stream_reply(self, gemini_messages, context, model: genai.GenerativeModel):
        res = model.generate_content(gemini_messages, stream=True)
        for chunk in res:
            if chunk.text:
                try:
                    context.get("channel").send(Reply(ReplyType.TEXT, chunk.text.replace("\n", "").replace("**", "")), context)
                except:
                    context.get("channel").send(Reply(ReplyType.TEXT, chunk.text.replace("\n", "").replace("**", "")), context)
        return res
    
    @staticmethod
    def GeminiApiConfig():
        keys = conf().get("gemini_api_key")
        keys = keys.split("|")
        keys = [key.strip() for key in keys]
        if not keys:
            raise Exception("Please set a valid API key in Config!")
        api_key = random.choice(keys)
        genai.configure(api_key=api_key)
