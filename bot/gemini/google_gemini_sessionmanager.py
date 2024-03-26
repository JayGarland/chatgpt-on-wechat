from bot.session_manager import SessionManager, Session
from config import conf
from common.log import logger

class GeminiSession(Session):
    def __init__(self, session_id, system_prompt=None, model="gpt-3.5-turbo"):
        super().__init__(session_id, system_prompt)
        self.model = model
        self.promptupdated = False
        self.reset()

    def set_system_prompt(self, system_prompt):
        self.system_prompt = system_prompt
        self.promptupdated = True
        self.reset()

class GeminiSessionManager(SessionManager):
    def session_query(self, query, session_id):
        session = self.build_session(session_id)
        if self.sessions[session_id].promptupdated:
            query = self.sessions[session_id].system_prompt + f"\n\n\n{query}"
        session.add_query(query)
        self.sessions[session_id].promptupdated = False
        try:
            max_tokens = conf().get("conversation_max_tokens", 1000)
            total_tokens = session.discard_exceeding(max_tokens, None)
            logger.debug("prompt tokens used={}".format(total_tokens))
        except Exception as e:
            logger.warning("Exception when counting tokens precisely for prompt: {}".format(str(e)))
        return session