# Fase 5 — Monitoraggio, grafici e alert

## Obiettivo
Tenere traccia nel tempo dello stato dei router (CPU, RAM, traffico, uptime) e
notificare l'utente in caso di problemi.

## Prerequisiti
Fase 2 (VPN) terminata almeno per i router da monitorare.

## Task da eseguire

1. Polling periodico (Celery beat, intervallo configurabile, default 1-5 minuti):
   - Connessione via `librouteros` sull'IP VPN
   - Raccogliere: CPU load, uso memoria, uptime, contatori traffico per interfaccia,
     temperatura (se disponibile sul modello)
   - Salvare le metriche in una tabella time-series su PostgreSQL (per 4-20 router il
     volume di dati è gestibile senza bisogno di InfluxDB o simili)

2. Gestione irraggiungibilità:
   - Se il polling fallisce N volte consecutive (soglia configurabile), marcare il
     router come `offline` e generare un evento di alert

3. Alert:
   - Integrazione Telegram Bot API (gratuita): token bot salvato in config, chat_id
     dell'utente salvato nelle impostazioni
   - In alternativa/aggiunta: email via Django (SMTP già configurabile)
   - Alert su: router offline, CPU/temperatura sopra soglia configurabile, backup
     fallito (collegamento con Fase 4)
   - Anti-spam: non rimandare lo stesso alert ogni ciclo di polling, solo al cambio di
     stato o con un cooldown configurabile

4. Interfaccia utente:
   - Dashboard con vista d'insieme di tutti i router (stato, ultimo check, CPU/RAM
     correnti)
   - Grafici storici per singolo router (Chart.js o Recharts): CPU/RAM nel tempo,
     traffico per interfaccia
   - Pagina impostazioni per soglie di alert e canali di notifica

## Criteri di completamento
- Le metriche di un router di test vengono raccolte e visualizzate in un grafico
- Spegnendo/scollegando il router di test, arriva una notifica entro il tempo atteso
- Le soglie di alert sono modificabili da interfaccia senza toccare il codice

## Note
Se emergono dubbi su quali metriche aggiuntive valga la pena raccogliere (es. clienti
DHCP connessi, stato wireless), annotalo in `fase_8_modifiche_rifinitura.md` invece di
espandere lo scope qui.
