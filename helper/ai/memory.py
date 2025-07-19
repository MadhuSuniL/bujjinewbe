from datetime import datetime
from sqlalchemy import create_engine
from django.conf import settings
from langchain_core.messages import trim_messages
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage
from langchain_community.chat_message_histories import SQLChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from auth_app.models import User
from helper.classes import TrimMessages

class Memory:
    def __init__(self, sql_history_obj : SQLChatMessageHistory,  max_tokens: int):
        self.trim_messages = TrimMessages()
        self.max_tokens = max_tokens
        self.sql_history_obj = sql_history_obj
        self.messages = self.get_trimmed_messages()
    
    def get_trimmed_messages(self):
        return self.trim_messages.invoke(self.sql_history_obj.messages, self.max_tokens)
        
    def get_timestamp(self):
        return datetime.now().strftime("%A, %B %d, %Y - %I:%M %p")

    def add_user_message(self, message: HumanMessage):
        self.sql_history_obj.add_user_message(message)

    def add_ai_message(self, message: AIMessage):
        self.sql_history_obj.add_ai_message(message)
        
    def add_tool_message(self, message: ToolMessage):
        self.sql_history_obj.add_message(message)
        
    def add_message(self, message: BaseMessage):
        self.sql_history_obj.add_message(message)
                
    @classmethod
    def get_memory(cls, session_id:str, user_id:str, max_tokens: int) -> BaseChatMessageHistory:
        engine = create_engine(settings.MEMORY_CONNECTION_STRING)
        user : User = User.objects.get(id=user_id)
        user_memory_table_name = f"{user.first_name}_chat_memory_{user_id.split('-')[0]}".replace(' ', '_').replace('-', '_').lower()
        message_history = SQLChatMessageHistory(session_id=session_id, connection=engine, table_name = user_memory_table_name)
        message_history_trimmed = cls(message_history, max_tokens) if len(message_history.messages) > 0 else message_history
        return message_history_trimmed