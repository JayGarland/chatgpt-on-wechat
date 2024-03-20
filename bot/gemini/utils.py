from common.log import logger
from config import conf
from bridge.reply import Reply, ReplyType
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

def wrap_promo_msg(context, reply_text):
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