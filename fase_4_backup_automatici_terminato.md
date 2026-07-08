# Fase 4 — Backup automatici configurabili

## Obiettivo
Backup periodici e configurabili per router, salvati in modo sicuro e consultabili
dalla dashboard.

## Prerequisiti
Fase 1 (anagrafica) e almeno Fase 2 (VPN) terminate per i router su cui si vuole
attivare il backup. Idealmente anche Fase 3 (accesso solo via VPN).

## Task da eseguire

1. Scheduling dinamico:
   - Usare `django-celery-beat` per permettere intervalli di backup diversi per
     ciascun router, modificabili da interfaccia (non hardcoded nel codice)
   - Campo già previsto in Fase 1 (`intervallo_backup`): collegarlo a un
     `PeriodicTask` per router

2. Task Celery di backup, per ogni router:
   - Connessione via `librouteros` sull'IP VPN (mai IP pubblico)
   - Eseguire `/system/backup/save` (formato binario, ripristinabile 1:1) e
     `/export` (formato testo, leggibile/diffabile)
   - Scaricare i file generati (via API o SFTP)
   - Upload su Hetzner Object Storage (stesso bucket usato da Squadfy, in una cartella
     dedicata `mikrotik-backups/<nome-router>/`)
   - Naming file con timestamp ISO, es. `router-nome_2026-07-06T10-00.backup`

3. Retention:
   - Campo configurabile (es. "tieni ultimi N backup" o "tieni backup ultimi X giorni")
   - Task di pulizia periodico che rimuove i backup più vecchi della soglia

4. Interfaccia utente:
   - Vista storico backup per router (data, dimensione, link download)
   - Pulsante "Backup manuale ora" oltre allo scheduling automatico
   - Indicatore se l'ultimo backup pianificato è fallito (utile per Fase 5/alert)

## Criteri di completamento
- Un router di test produce un backup automatico all'intervallo configurato
- Il file è scaricabile dalla dashboard e corrisponde a un backup RouterOS valido
- Cambiare l'intervallo di un router non richiede riavvio del servizio
- I backup vecchi oltre la soglia di retention vengono rimossi automaticamente

## Note
Se emergono dubbi su crittografia dei backup a riposo nell'object storage (già cifrato
lato Hetzner o serve doppia cifratura applicativa), annotalo in
`fase_8_modifiche_rifinitura.md`.
