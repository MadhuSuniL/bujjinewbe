from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.request import Request
from . import models, serializers
from helper.ai.custom_responses import DynamicCustomResponse
from helper.ai.system_prompts import summary_generator_prompt, highlights_generator_prompt

class ConversationViewSet(viewsets.ModelViewSet):
    serializer_class = serializers.ConversationSerializer
    queryset = models.Conversation.objects.all()
    
    def get_queryset(self):
        request = self.request
        queryset = super().get_queryset().filter(user = request.user).order_by('-used_at') 
        limit = self.request.GET.get('limit', 30)
        if self.action == "list":
            return queryset[:limit]
        return queryset
    
class ConversationMessageListView(APIView):
    
    def get(self, request : Request, conversation_id : str, *args, **kwargs):
        conversation = models.Conversation.objects.get(id=conversation_id, user = request.user)
        messages = conversation.messages.all() if hasattr(conversation, 'messages') else []
        serializer = serializers.MessageSerializer(messages, many=True)
        return Response(serializer.data)


class MessageInsightsView(APIView):
    
    def post(self, request, insight):
        content = request.data.get("content", "")
        system_prompt = summary_generator_prompt if insight == "summary" else highlights_generator_prompt
        insight_generator = DynamicCustomResponse(system_message=system_prompt, params_trim_length=0, params={"content" : content})
        response = insight_generator.invoke()
        return Response(response.content)
        


class ShareConversationCreate(APIView):
        
    def post(self, request, share_id = None):
        conversation_id = request.data.get("conversation_id")
        share = models.ShareConversation.objects.create(conversation_id = conversation_id)
        return Response({"share_id" : share.id})

class ShareConversationCreateAndClone(APIView):
            
    def get(self, request, share_id):
        share = models.ShareConversation.objects.get(id = share_id)
        if share.is_expired:
            return Response({"detail" : "Share ID Expired!"}, status=400)
        conversation = share.conversation
        messages = conversation.messages
        data = {
            "conversation" : serializers.ConversationSerializer(conversation).data,
            "messages" : serializers.MessageSerializer(messages, many = True).data
        }
        return Response(data)


        
    def patch(self, request, share_id):
        current_user = request.user
        share = models.ShareConversation.objects.get(id = share_id)
        if share.is_expired:
            return Response({"detail" : "Share ID Expired!"}, status=400)
        conversation = share.conversation
        messages = conversation.messages.all()
        
        # Copy Conversation
        copied_conversation = models.Conversation.objects.create(title = conversation.title, user = current_user)        
        
        # Copy messages
        copied_messages = []
        for message in messages:
            copied_messages.append(models.Message(
                conversation = copied_conversation,
                author = message.author,
                content = message.content,
                status = message.status,
                sources = message.sources,
                metadata = message.metadata,
                prompts = message.prompts,
                summary = message.summary
            ))
        models.Message.objects.bulk_create(copied_messages)
        return Response({"conversation_id" : copied_conversation.id})
 