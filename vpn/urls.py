from django.urls import path

from . import views

urlpatterns = [
    path('router/<int:pk>/genera-script/', views.GenerateVpnScriptView.as_view(), name='vpn-generate-script'),
    path('router/<int:pk>/salva-chiave/', views.SaveWireguardPublicKeyView.as_view(), name='vpn-save-public-key'),
    path('router/<int:pk>/registra-peer/', views.RegisterPeerView.as_view(), name='vpn-register-peer'),
    path('router/<int:pk>/test-connessione/', views.TestVpnConnectionView.as_view(), name='vpn-test-connection'),
]
