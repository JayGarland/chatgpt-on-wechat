from common.log import logger
import asyncio
import pathlib
from bot.gemini.documentRead import *

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

async def build_docx_msg(file_path):
    loop_local = asyncio.get_event_loop()
    ext = pathlib.Path(file_path).suffix
    try:
        if ext == ".pptx":
            text = await loop_local.run_in_executor(None, read_pptx_text, file_path)
            docxMessage = f'\n[user](#document_context_pptx_file)\n```\n{text}\n```\n\n'
        elif ext == ".pdf":
            text = await loop_local.run_in_executor(None, read_pdf_text, file_path)
            docxMessage = f'\n[user](#document_context_pdf_file)\n```\n{text}\n```\n\n'
        elif ext == ".docx":
            text = await loop_local.run_in_executor(None, read_docx_text, file_path)
            docxMessage = f'\n[user](#document_context_docx_file)\n```\n{text}\n```\n\n'
        else:
            logger.error("Unsupported file type")
            return f"我文化水平低,只认得docx,pdf,pptx类型的文档 \U0001F605"
        if len(text.split()) < 2:
            return f"我阅读能力差,这篇文章我看不懂咧 \U0001F605" 
        return docxMessage
    except Exception as e:
        logger.error(e)