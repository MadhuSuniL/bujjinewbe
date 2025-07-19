from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    NoteCollectionViewSet,
    NoteViewSet,
)

router = DefaultRouter()
router.register(r'notes', NoteViewSet)
router.register(r'note_collections', NoteCollectionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
