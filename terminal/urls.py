from django.urls import path

from . import views

urlpatterns = [
    path('router/<int:pk>/terminale/', views.TerminalView.as_view(), name='router-terminal'),
]
