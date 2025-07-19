from rest_framework import viewsets, response, generics
from .models import Note, NoteCollections
from .serializers import (
    NoteCollectionSerializer,
    NoteSerializer,
)
from helper.ai.system_prompts import note_heading_and_collection_name_generator_prompt
from helper.ai.custom_responses import DynamicCustomResponse

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer
    
    def create(self, request):
        current_user = request.user
        notes = request.data.get("notes", [])
        user_headings = self.queryset.filter(user = current_user).values_list("heading", flat=True)
        user_collections = NoteCollections.objects.filter(user = current_user).values_list("name", flat=True)
        system_message = note_heading_and_collection_name_generator_prompt.format(exist_headings = ", ".join(user_headings), exist_collections = ", ".join(user_collections))
        dynamic_response = DynamicCustomResponse(system_message=system_message, params={"notes" : notes}, params_trim_length = 0)
        result = dynamic_response.invoke()
        heading, collection_name = result.content.split(" | ")
        
        # Create Note
        note, _ = Note.objects.get_or_create(heading = heading, user = current_user)
        note.points = list(set([*note.points, *notes]))
        note.save()
        
        # Create Note Collection
        collection, _ = NoteCollections.objects.get_or_create(name = collection_name, user = current_user)        
        if not collection.notes.filter(heading = heading).exists():
            collection.notes.add(note)
            collection.save()            
        print(system_message)
        return response.Response({"detail" : "Notes Saved!"})
        


class NoteCollectionViewSet(viewsets.ModelViewSet):
    queryset = NoteCollections.objects.all()
    serializer_class = NoteCollectionSerializer
    
    
    def retrieve(self, request, *args, **kwargs):
        object = self.get_object()
        collection_data = NoteCollectionSerializer(object).data
        collection_data['notes'] = NoteSerializer(object.notes, many = True).data
        return response.Response(collection_data)