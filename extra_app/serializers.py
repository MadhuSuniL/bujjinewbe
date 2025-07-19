from rest_framework import serializers
from .models import Note, NoteCollections

class NoteCollectionSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default = serializers.CurrentUserDefault())
    class Meta:
        model = NoteCollections
        fields = '__all__'


class NoteSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default = serializers.CurrentUserDefault())
    class Meta:
        model = Note
        fields = '__all__'