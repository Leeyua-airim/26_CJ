from django.urls import path

from . import views

app_name = "gpt_chat"

urlpatterns = [
    path("", views.chat_page, name="chat_page"),
    path("api/send/", views.send_message_api, name="send_message_api"),
]
