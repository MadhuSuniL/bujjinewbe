from django.db import models
from langchain_core.documents import Document


class MessageManager(models.Manager):
    """Manager for creating human and assistant messages."""

    def _create_message(self, conversation_id: str, role: str, name: str, content_type: str = 'text', content: str | list = '', status: str | None = None):
        """Internal helper to create a message with given role, content, and metadata."""
        
        message_data = {
            'conversation_id': conversation_id,
            'author': {'role': role, 'name': name},
            'content': {'content_type': content_type, 'content': content},
        }
        if status:
            message_data['status'] = status
        return self.create(**message_data)

    def create_human_message(self, conversation_id: str, content_type: str = 'text', content: str | list = ''):
        """Creates a message authored by a human."""
        
        return self._create_message(
            conversation_id,
            role='human',
            name='Human',
            content_type=content_type,
            content=content,
            status='complete'
        )

    def create_assistant_message(self, conversation_id: str, content_type: str = 'text', content: str | list = ''):
        """Creates a message authored by the assistant."""
        
        return self._create_message(
            conversation_id,
            role='assistant',
            name='GPT-Suite',
            content_type=content_type,
            content=content
        )