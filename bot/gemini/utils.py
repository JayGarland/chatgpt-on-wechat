from common.log import logger


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