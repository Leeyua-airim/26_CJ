from django.contrib import admin
from django.urls import path, include
from core import views as core_views


from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # allauth
    path('accounts/', include('allauth.urls')),
    
    # core 앱의 URL 포함
    path('', include('core.urls')),  
    path('chat/', include('gpt_chat.urls')),
    
    # /app/는 core.urls가 담당 (기존 구조 유지)
    path("", include("core.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)