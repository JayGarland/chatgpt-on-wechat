"""
Google gemini bot

@author zhayujie + rajayoux
@Date 2023/12/15 + 3/20/2024
"""
# encoding:utf-8

from bot.bot import Bot
from bot.session_manager import SessionManager
from bridge.context import ContextType, Context
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf
from bot.baidu.baidu_wenxin_session import BaiduWenxinSession
from bot.gemini.llm import model, img_model
from bot.gemini.utils import *
from PIL import Image
from common import memory
import io



# OpenAI对话模型API (可用)
class GoogleGeminiBot(Bot):
    def __init__(self):
        super().__init__()
        # 复用文心的token计算方式
        self.sessions = SessionManager(BaiduWenxinSession, model=conf().get("model"))

    def reply(self, query: str, context: Context = None) -> Reply:
        try:
            if context.type != ContextType.TEXT:
                logger.warn(f"[Gemini] Unsupported message type, type={context.type}")
                return Reply(ReplyType.TEXT, None)
            logger.info(f"[Gemini] query={query}")
            session_id = context["session_id"]
            session = self.sessions.session_query(query, session_id)
            reply = None
            clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])
            if query.lower() in clear_memory_commands:
                self.sessions.clear_session(session_id)
                reply = Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                reply = Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置": 
                #TODO when use this, bot in particular group chat will switch persona
                reply = Reply(ReplyType.INFO, "配置已更新")
            elif query == "撤销" or query == "撤回" or query.lower() == "revoke":
                session.messages.pop()
                users_arr = [obj for obj in session.messages if obj['role'] == 'user']
                if len(users_arr) < 1:
                    passivereply = Reply(ReplyType.INFO, "没有可撤回的消息!")
                    return passivereply
                session.messages = session.messages[:list(session.messages).index(users_arr[-1])]#FIXME, canceled unexpected multiple lines
                cliped_msg = clip_message(users_arr[-1]['content'])
                reply = Reply(ReplyType.INFO, f"该条消息已撤销!\nThe previous message is cancelled. \n\n({cliped_msg})")
            if reply:
                return reply
            session = self.sessions.session_query(query, session_id)
            preset = self.construct_preset(context)
            gemini_messages = preset + self._convert_to_gemini_messages(self._filter_messages(session.messages))
            logger.info(gemini_messages)
            # image process
            img_cache = memory.USER_IMAGE_CACHE.get(session_id)
            if img_cache:
                img = self.process_img(session_id, img_cache)
                # logger.info(img)
                response = img_model.generate_content([query, img]) #when use the vision no persona
            else:
                response = trygen(model, gemini_messages)
            # logger.debug(response)
            reply_text = response.text
            self.sessions.session_reply(reply_text, session_id)
            logger.info(f"[Gemini] reply={reply_text}")
            if context["isgroup"] and not context["stream"] and not context["voice"]:
                reply_text += "\n\n" + self.bot_statement
            if len(session.messages) == 3:
                return self.wrap_promo_msg(context, reply_text)
            return Reply(ReplyType.TEXT, reply_text)
        except Exception as e:
            import traceback
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

    def _filter_messages(self, messages: list):
        res = []
        turn = "user"
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
    
    def init_prompt_botstatement(self, context):
        persona = None
        pre_reply = None
        
        for setting_pairs in conf().get("customerSet"):
            for key, cusprompt in dict(setting_pairs).items():
                if key == context["session_id"]:
                    persona = cusprompt
                    pre_reply = setting_pairs["pre_reply"]
                    self.bot_statement = setting_pairs["botstatement"]#FIXME seprate botstatement and other params from the settings as the cusprompt doesn't support multi lines writing
                    conf().__setitem__("voicespecies", "zh-CN-liaoning-XiaobeiNeural")
                    break
        if not persona:
            persona = conf().get("character_desc")
            pre_reply = conf().get("pre_reply")
            self.bot_statement = conf().get("sydney_statement")
            conf().__setitem__("voicespecies", "zh-CN-XiaoxiaoNeural") #zh-CN-XiaoxiaoNeural optional, more matual
        if not context["isgroup"]:
            self.bot_statement = ""
        return persona, pre_reply
    
    def wrap_promo_msg(self, context, reply_text):
        credit = conf().get("sydney_credit")
        if not context["isgroup"] and context["stream"]:
            reply_text += credit
        else: 
            reply_text += "\n\n" + credit
        qridimg = open('.\wechatID.jpg', 'rb')
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
            with open(path, "rb") as f:
                img_bytes = f.read()
            img = Image.open(io.BytesIO(img_bytes))
            memory.USER_IMAGE_CACHE[session_id] = None
            return img
        except Exception as e:
            logger.exception(e)