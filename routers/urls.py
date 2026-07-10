from django.urls import path

from . import views

urlpatterns = [
    path('', views.RouterListView.as_view(), name='router-list'),
    path('router/nuovo/', views.RouterCreateView.as_view(), name='router-create'),
    path('router/rileva/', views.RouterProbeView.as_view(), name='router-probe'),
    path('router/<int:pk>/', views.RouterDetailView.as_view(), name='router-detail'),
    path('router/<int:pk>/modifica/', views.RouterUpdateView.as_view(), name='router-update'),
    path('router/<int:pk>/elimina/', views.RouterDeleteView.as_view(), name='router-delete'),
]
