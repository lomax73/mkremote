# Fase 7 — Accesso VPN personale dell'utente

## Obiettivo
Permettere all'utente (non solo al server) di collegarsi alla subnet VPN privata da
PC o telefono, raggiungendo tutti i router con un solo profilo WireGuard.

## Prerequisiti
Fase 2 terminata (hub WireGuard sul VPS funzionante con almeno un router collegato).

## Task da eseguire

1. Gestione peer "umani" nel VPS:
   - Un peer WireGuard per dispositivo personale (es. laptop, telefono), IP nella
     fascia riservata `.2`-`.9` (vedi pianificazione subnet di Fase 0)
   - Generazione della coppia di chiavi lato server per il client (per un client umano,
     a differenza del router, è accettabile generare la chiave sul server e consegnarla
     all'utente, oppure generarla lato client se si preferisce non farla mai transitare
     dal server — valutare in base a comodità vs sicurezza)

2. Interfaccia utente:
   - Sezione "I miei dispositivi VPN" nella dashboard
   - Pulsante "Aggiungi dispositivo" → genera file `.conf` scaricabile e/o QR code
     (utile per l'app mobile WireGuard) da leggere con lo smartphone
   - Possibilità di revocare un dispositivo (rimuove il peer dal server)

## Criteri di completamento
- L'utente riesce a collegarsi da telefono o PC con l'app WireGuard ufficiale usando
  il profilo generato
- Da quel profilo raggiunge (ping) sia il VPS sia i router già collegati
- Revocare un dispositivo ne disattiva immediatamente l'accesso

## Note
Se emerge il dubbio se generare le chiavi client lato server o lato client, annotalo
in `fase_8_modifiche_rifinitura.md` con la scelta di default adottata.
