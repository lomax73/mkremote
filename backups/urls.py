from django.urls import path

from . import views

urlpatterns = [
    path('backup/', views.BackupOverviewView.as_view(), name='backup-overview'),
    path('router/<int:pk>/backup/', views.BackupListView.as_view(), name='backup-list'),
    path('router/<int:pk>/backup/ora/', views.BackupNowView.as_view(), name='backup-now'),
    path('router/<int:pk>/backup/<int:backup_id>/scarica/', views.BackupDownloadView.as_view(), name='backup-download'),
    path('router/<int:pk>/backup/<int:backup_id>/elimina/', views.BackupDeleteView.as_view(), name='backup-delete'),
    path('router/<int:pk>/backup/log/<int:run_id>/', views.BackupRunDetailView.as_view(), name='backup-run-detail'),
    path('router/<int:pk>/backup/log/<int:run_id>/stato/', views.BackupRunStatusView.as_view(), name='backup-run-status'),
]
