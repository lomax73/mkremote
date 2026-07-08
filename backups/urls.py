from django.urls import path

from . import views

urlpatterns = [
    path('router/<int:pk>/backup/', views.BackupListView.as_view(), name='backup-list'),
    path('router/<int:pk>/backup/ora/', views.BackupNowView.as_view(), name='backup-now'),
    path('router/<int:pk>/backup/<int:backup_id>/scarica/', views.BackupDownloadView.as_view(), name='backup-download'),
]
