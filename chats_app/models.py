from datetime import timedelta
from django.utils import timezone
from collections import defaultdict
from django.conf import settings
from django.db import models
from helper.models import UUIDPrimaryKey, TimeLine
from chats_app.managers import MessageManager

def str_default_dict():
   return defaultdict(str)
    
class Conversation(UUIDPrimaryKey, TimeLine):
    title = models.CharField(max_length=255, default="New chat")
    
    is_pinned = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_starred = models.BooleanField(default=False)

    used_at = models.DateTimeField(null=True, blank=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    
    def update_used_at(self):
        self.used_at = timezone.now()
        self.save(update_fields=['used_at'])
        
    class Meta:
        ordering = ['-used_at']

class Message(UUIDPrimaryKey, TimeLine):

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name= 'messages')  

    author = models.JSONField(default=str_default_dict)  # role, name, metadata
    content = models.JSONField(default=str_default_dict)  # content_type, content
    status = models.CharField(max_length=50, default="pending")  # pending, in_progress, completed, failed
    sources = models.JSONField(default=str_default_dict, blank=True)  # retrived_contexts, self_discussion_context
    metadata = models.JSONField(default=str_default_dict, blank=True)  # finish_reason, finished_duration_sec, model_slug, token_usage
    prompts = models.JSONField(default=str_default_dict, blank=True) # system, user
    summary = models.TextField(blank=True, null=True)
    

    def update_status(self, status : str, metadata : dict):
        self.status = status

        if self.created_at:
            time_diff = timezone.now() - self.created_at            
            completion_time_in_seconds = time_diff.total_seconds()
            completion_time_in_milliseconds = completion_time_in_seconds * 1000
            metadata.update({'completion_time' : completion_time_in_milliseconds}) 

        if metadata:
            self.metadata.update(metadata)
        self.save()
        
    def update_self_dicussion_contexts(self, contexts):
        self.sources['self_discussion_context'] += contexts
    
    def update_content(self, content):
        self.content['content'] += content
        
    def update_retrived_contexts(self, context : dict[str:str]):
        self.sources['retrived_contexts'] = context
        

    def add_prompts(self, prompts : dict):
        self.prompts.update(prompts)
        self.save()

    objects : MessageManager = MessageManager()

    class Meta:
        ordering = ['created_at']
        
    
class VectorStoreWikipediaFlag(UUIDPrimaryKey, TimeLine):
    page_title = models.CharField(max_length=500, unique=True)
    is_done = models.BooleanField(default=False)
    
    
    @classmethod
    def flag(cls, page_title : str):
        return cls.objects.get_or_create(page_title = page_title, is_done = True)
    
    def done(self):
        self.is_done = True
        self.save()
        

class ShareConversation(UUIDPrimaryKey, TimeLine):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE)
    
    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=60)