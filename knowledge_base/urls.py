from django.urls import path
from . import views
from . import api_views

urlpatterns = [
    # 화면
    path("project/<int:project_id>/", views.kb_project, name="kb_project"),

    # API
    path("api/project/<int:project_id>/upload/", api_views.upload_document, name="kb_upload_document"),
    path("api/project/<int:project_id>/documents/", api_views.document_list, name="kb_document_list"),
    path("api/document/<int:document_id>/chunks/", api_views.chunk_list, name="kb_chunk_list"),

    path("api/project/<int:project_id>/index/", api_views.index_project_chunks, name="kb_index_project_chunks"),
]
