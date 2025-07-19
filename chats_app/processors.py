import time
import json
import datetime
from django.http import StreamingHttpResponse
from rest_framework.request import Request
from langchain_core.messages import AIMessage, ToolMessage
from langchain_groq import ChatGroq
from workflow_graphs.bujji.workflow import graph
from workflow_graphs.bujji.prompts import SYSTEM_PROMPT
from . import serializers, models
from auth_app.models import User
from helper.ai.system_prompts import chat_title_generator_prompt
from helper.ai.custom_responses import DynamicCustomResponse

class BujjiConversationResponseProcessor:
    def __init__(self, request : Request):
        self.current_user : User = request.user
        self.current_date = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        self.request = request
        self.body = request.data
        self.conversation_id : str = self.body.get("conversation_id")
        self.query : str = self.body.get("query", "Hello")
        self.kids_mode : str = self.body.get("kids_mode", "Off")
        self.system_prompt : str = SYSTEM_PROMPT.format(kids_mode = 'ON' if self.kids_mode else 'OFF')
        self.model = ChatGroq(model='llama-3.3-70b-versatile')
        
    def create_human_message(self, conversation_id : str, content_type : str = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_human_message(conversation_id, content_type, content)
        
        
    def create_assistant_message(self, conversation_id : str, content_type = 'text', content : str | list = '') -> models.Message:
        return models.Message.objects.create_assistant_message(conversation_id, content_type, content= content)    
    
    
    def _create_and_send_assistant_message(self, content_type = 'text'):
        self.messages[1] = self.create_assistant_message(
            self.conversation_id, content='', content_type=content_type
        )
        self.messages[1].add_prompts({'system': self.system_prompt, 'user': self.query})
        return self._send_event(
            event="assistant_message",
            t="messages",
            p="messages",
            o="add",
            v=serializers.MessageSerializer(self.messages[1]).data
        )
    

    def _send_event(self, event, t, p, o, v):
        time.sleep(0.01)
        return f"event: {event}\ndata: {json.dumps({'t': t, 'p': p, 'o': o, 'v': v})}\n\n"


    def process_conversation(self):
        # Get or Create the conversation
        self.conversation, self.with_new_conversation = models.Conversation.objects.get_or_create(id=self.conversation_id, defaults={'user_id': self.current_user.id})
        self.conversation.update_used_at()
        self.conversation_id = self.conversation.id        

    def create_required_messages(self):
        self.messages : list[models.Message] = [
            self.create_human_message(self.conversation_id, content=self.query, content_type='text'),
            None
        ]        
            
    def create_initial_state(self):
        self.initial_state = {
            'model' : self.model,
            'user_id': str(self.current_user.id),
            'conversation_id': str(self.conversation_id),
            'user_query': self.query,
            'messages': [],
            'new_messages': [],
            'memory_messages': [],
            'kids_mode': self.kids_mode,
            '_verbose': True,
        }
        
        
    def init_proccessing(self):
        self.process_conversation()
        self.create_required_messages()
        self.create_initial_state()
    
    
    def process_response_with_events(self):
        tool_calling = False
        tool_index = 0
        response_metadata = {}

        try:
            if self.with_new_conversation:
                yield self._send_event(
                    event="new_conversation",
                    t="conversations",
                    p="conversation",
                    o="add",
                    v=serializers.ConversationSerializer(self.conversation).data
                )
            
            # yield self._send_event(
            #         event="human_message",
            #         t="messages",
            #         p="messages",
            #         o="add",
            #         v=serializers.MessageSerializer(self.messages[0]).data
            #     )
                
            for message, message_data in graph.stream(self.initial_state, stream_mode='messages'):
                message : AIMessage | ToolMessage = message
                node = message_data.get('langgraph_node')
                content = message.content or ""
                response_metadata = message.response_metadata or {}
                retrived_contexts = []

                if hasattr(message, 'usage_metadata') and message.usage_metadata:
                    response_metadata.update(message.usage_metadata)

                tool_calls = getattr(message, 'tool_calls', [])

                if node == 'init_node':
                    ...

                elif node == 'call_model':                        
                    if tool_calling:
                        tool_calling = False
                        yield self._send_event("tool_call", "status", "tool_call", "update", False)

                    if content:
                        if self.messages[1] is None:
                            yield self._create_and_send_assistant_message()

                        self.messages[1].update_content(content)
                        yield self._send_event(
                            event="delta",
                            t="messages",
                            p="message/content/content",
                            o="append",
                            v = content
                        )
 
                    if tool_calls:
                        yield self._send_event("tool_call", "status", "tool_call", "update", True)
                        self.messages[1] = self.create_assistant_message(self.conversation_id, content='', content_type='tool_call')
                        self.messages[1].add_prompts({'system' : self.system_prompt, 'user' : self.query})
                        self.messages[1].content.update({"tool_calls": tool_calls})
                        self.messages[1].save()
                        
                    if response_metadata:
                        self.messages[1].update_status('complete', metadata=response_metadata)
                        yield self._send_event("delta", "messages", "message/status", "add", 'complete')
                        

                elif node == 'tool_node':
                    if not tool_calling:
                        tool_calling = True
                        tool_index = 0
                        self.messages[1] = self.create_assistant_message(self.conversation_id, content='')
                        self.messages[1].add_prompts({'system' : self.system_prompt, 'user' : self.query})
            
                        yield self._send_event(
                            event="assistant_message",
                            t="messages",
                            p="messages",
                            o="add",
                            v=serializers.MessageSerializer(self.messages[1]).data
                        )

                    if content:
                        path = f"message/sources/retrived_contexts"
                        data = [*retrived_contexts, {"name": message.name, "content": content}] if tool_index == 0 else {"name": message.name, "content": content}
                        operation = "add" if tool_index == 0 else "append"
                        self.messages[1].update_retrived_contexts(data)
                        yield self._send_event("delta", "messages", path, operation, data)
                        tool_index += 1      
                        retrived_contexts.extend(data) if operation == 'add' else retrived_contexts.append(data)      
                        # print("--------------------------", retrived_contexts)
            
            if self.with_new_conversation:
                chat_title_generator = DynamicCustomResponse(chat_title_generator_prompt, params={"user_query": self.messages[0].content['content'], "assistant_response": self.messages[1].content['content']})
                event = "conversation_title"
                t = "conversations"
                p = "conversation/title"
                operation = "add"
                v = ""

                yield self._send_event(event=event, t=t, p=p, o=operation, v=v)

                for chunk in chat_title_generator.stream():
                    yield self._send_event(
                        event="delta",
                        t="conversations",
                        p="conversation/title",
                        o="append",
                        v=chunk.content
                    )
                    v += chunk.content
                self.conversation.title = v
                self.conversation.save()
                
            # Calcuate the model token cost and will update that in message.
            
            yield "event: done\ndata: [DONE]\n\n"

        except Exception as e:
            print(e)
            if self.messages[1] is not None:
                self.messages[1].update_status('error', metadata=response_metadata)
            yield self._send_event("delta", "messages", "message/status", "add", 'error')
            yield self._send_event("error", "error", "error", "add", str(e))
            raise e

