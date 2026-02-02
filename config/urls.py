from django.contrib import admin
from django.urls import path, include
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    # allauth
    path('accounts/', include('allauth.urls')),
    # 로그인 후 랜딩
    path('app/', core_views.app_home, name='app_home'),
]
