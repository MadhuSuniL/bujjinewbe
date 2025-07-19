from rest_framework import serializers
from .models import Message, Conversation


class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = "__all__"

        
class MessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='conversation.user.id')
    user_full_name = serializers.ReadOnlyField(source='conversation.user.full_name')

    class Meta:
        model = Message
        fields = '__all__'
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['conversation'] = str(data['conversation'])
        data['user'] = str(data['user'])
        return data
     
        
class ConversationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Conversation
        fields = '__all__'
        
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['user'] = str(data['user'])
        return data
        