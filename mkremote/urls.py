from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('help/', views.HelpView.as_view(), name='help'),
    path('', include('routers.urls')),
    path('', include('vpn.urls')),
    path('', include('backups.urls')),
    path('', include('terminal.urls')),
    path('', include('monitoring.urls')),
]
