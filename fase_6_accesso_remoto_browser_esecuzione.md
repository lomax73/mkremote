# Fase 6 — Accesso remoto da browser

## Obiettivo
Poter operare su un router direttamente dal browser, senza aprire WinBox o un client
SSH separato.

## Prerequisiti
Fase 2 (VPN) terminata per il router. Idealmente anche Fase 3 (accesso solo via VPN).

## Task da eseguire

1. Terminale SSH nel browser:
   - Backend: Django Channels (già in requirements dalla Fase 0) + `asyncssh` per
     aprire una sessione SSH verso l'IP VPN del router, esposta come WebSocket
   - Frontend: `xterm.js` collegato al WebSocket, renderizzato in una vista dedicata
     per router
   - Autenticazione: il backend usa le credenziali cifrate salvate in Fase 1, l'utente
     non le reinserisce ogni volta (ma valutare un secondo fattore/conferma esplicita
     prima di aprire la sessione, essendo un accesso privilegiato)
   - Log delle sessioni aperte (chi, quando, su quale router) per audit

2. Collegamento rapido a WebFig:
   - WebFig è già integrato in RouterOS (interfaccia web nativa su porta 80/443 del
     router)
   - Nella vista dettaglio router, un link diretto che apre WebFig sull'IP VPN
     (eventualmente in un iframe o in una nuova scheda, da valutare in base a
     limitazioni di embedding)

## Criteri di completamento
- Da un router di test, si apre un terminale funzionante nel browser e si possono
  eseguire comandi RouterOS
- Il link a WebFig raggiunge correttamente il router sull'IP VPN
- Le sessioni terminale vengono chiuse correttamente alla chiusura della pagina
  (nessuna sessione SSH orfana aperta sul router)

## Note
Se emergono dubbi su registrazione/replay delle sessioni terminale per audit più
approfondito, annotalo in `fase_8_modifiche_rifinitura.md`.
