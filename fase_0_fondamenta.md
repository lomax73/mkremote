# Fase 0 — Fondamenta infrastrutturali

## Obiettivo
Preparare il server e lo scheletro del progetto Django su cui costruire tutte le fasi
successive.

## Prerequisiti
Nessuno. Prima fase del progetto.

## Task da eseguire

1. Scaffolding progetto Django:
   - Nuovo progetto Django (nome app suggerito: `mikrotik_fleet`, ma valuta con l'utente)
   - App interne separate per dominio: `routers`, `vpn`, `backups`, `monitoring`, `accounts`
   - `requirements.txt` con: Django, djangorestframework, celery, redis, psycopg2-binary,
     django-celery-beat, django-cryptography (o equivalente), librouteros, asyncssh,
     channels, channels-redis
   - `.env` per i secret (SECRET_KEY, DB, Redis, chiave di cifratura master), mai committato

2. Infrastruttura server (VPS Hetzner, Ubuntu 24.04):
   - PostgreSQL, Redis, Nginx, Gunicorn (o Daphne/Uvicorn se serve ASGI per Channels)
   - WireGuard installato nativamente sul VPS (`wireguard-tools`)
   - Firewall del VPS (ufw/nftables): aprire solo 443 (dashboard) e la porta UDP scelta
     per WireGuard (es. 51820)

3. Pianificazione subnet VPN (da salvare in config, non hardcoded nel codice):
   - Subnet privata dedicata, es. `10.10.0.0/24`
   - `.1` riservato al VPS (hub)
   - `.2`-`.9` riservati a dispositivi personali (tuo laptop/telefono)
   - `.10` in su assegnati progressivamente ai router

4. Setup CI minimo/dev:
   - Ambiente virtuale, migrazioni iniziali, superuser Django
   - Verifica che Celery worker + Celery beat partano correttamente collegati a Redis

## Criteri di completamento
- Progetto Django avviabile in locale/dev con `runserver`
- Connessione a Postgres e Redis funzionante
- Celery worker che esegue un task di prova
- WireGuard installato sul VPS con interfaccia hub (`wg0`) attiva, anche se senza peer
- Struttura cartelle e app chiara, pronta per la Fase 1

## Note
- Non esporre ancora nulla in produzione: questa fase è infrastrutturale, non user-facing.
- Se emergono dubbi su hosting (stesso VPS di Squadfy vs VPS dedicato), annotalo in
  `fase_8_modifiche_rifinitura.md` invece di decidere da solo.
