from django.urls import path
from .views import app_home

urlpatterns = [
    path("app/", app_home, name="app_home"),
]