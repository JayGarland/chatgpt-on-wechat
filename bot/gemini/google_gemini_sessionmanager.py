from bot.session_manager import SessionManager, Session
from config import conf
from common.log import logger

class GeminiSession(Session):
    def __init__(self, session_id, system_prompt=None, model="gpt-3.5-turbo"):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.reset()

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.reset()

class GeminiSessionManager(SessionManager):
    def del_query(self, session_id):
        session = self.sessions[session_id]
        return session.messages.pop()