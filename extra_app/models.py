from django.db import models
from helper.models import UUIDPrimaryKey, TimeLine
from auth_app.models import User


class Note(UUIDPrimaryKey, TimeLine):
    heading = models.CharField(max_length=255)
    points = models.JSONField(default=list)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notes")

    def __str__(self):
        return self.heading


class NoteCollections(UUIDPrimaryKey, TimeLine):
    name = models.CharField(max_length=255)
    notes = models.ManyToManyField(Note, related_name="collections")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="note_collections")

    def __str__(self):
        return self.name
