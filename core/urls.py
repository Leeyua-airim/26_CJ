from django.urls import path, include
from .views import app_home, profile_complete, project_create

urlpatterns = [
    path("app/", app_home, name="app_home"),

    # Step 1: 프로필 완성
    path("app/profile/complete/", profile_complete, name="profile_complete"),

    # Step 2~: 확장 앱
    path("app/projects/create/", project_create, name="project_create"),
    path("app/agent/", include("agent_work.urls")),
    path("app/kb/", include("knowledge_base.urls")),
]
