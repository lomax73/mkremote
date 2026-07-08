from django.urls import path

from . import views

urlpatterns = [
    path('monitoraggio/', views.DashboardView.as_view(), name='monitoring-dashboard'),
    path('monitoraggio/impostazioni/', views.AlertSettingsView.as_view(), name='monitoring-settings'),
    path('monitoraggio/router/<int:pk>/', views.RouterMonitorDetailView.as_view(), name='monitoring-router-detail'),
    path('monitoraggio/router/<int:pk>/dati.json', views.RouterMetricsDataView.as_view(), name='monitoring-router-data'),
]
