from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import sse_views, views

router = DefaultRouter()
router.register('conversations', views.ConversationViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('bujji/completion/', sse_views.BujjiesponseSSEView.as_view(), name='bujji_response_sse'),  
    path('conversations/<conversation_id>/messages', views.ConversationMessageListView.as_view(), name='conversation_message_list'),  
    path('message/insights/<insight>/', views.MessageInsightsView.as_view(), name='message_insights'),  
    path("share/conversation/create", views.ShareConversationCreate.as_view(), name= "share_the_conversation"),
    path("share/conversation/details-and-clone/<share_id>", views.ShareConversationCreateAndClone.as_view(), name= "shared_conversation_details_and_clone"),
]
