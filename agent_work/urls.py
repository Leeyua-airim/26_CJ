from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # 화면
    path("project/<int:project_id>/", views.agent_project, name="agent_project"),

    # API
    path("api/project/<int:project_id>/conversations/", api_views.conversation_list_create, name="conversation_list_create"),
    path("api/conversation/<int:conversation_id>/messages/", api_views.message_list, name="message_list"),
    path("api/conversation/<int:conversation_id>/send/", api_views.send_message, name="send_message"),
]