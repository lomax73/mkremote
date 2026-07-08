# Fase 3 — Blocco dell'accesso pubblico

## Obiettivo
Una volta confermato che il tunnel WireGuard funziona (Fase 2), chiudere l'esposizione
di API/SSH/WebFig del router su internet, lasciando raggiungibili questi servizi solo
dalla subnet VPN privata.

## Prerequisiti
Fase 2 terminata: il router deve risultare `connesso` (test VPN superato) prima di
poter eseguire questa fase su di esso. Non applicare mai questa fase a un router il cui
stato non sia confermato connesso — rischio di perdere l'accesso al router.

## Task da eseguire

1. Generatore secondo script RouterOS (`.rsc`) da copiare/incollare, che:
   - aggiunge regole firewall che accettano connessioni su API (8728/8729), SSH,
     WebFig (porta 80/443 gestione) **solo** dalla subnet VPN (es. `10.10.0.0/24`)
   - droppa (o rifiuta) esplicitamente le stesse connessioni provenienti da altre
     sorgenti
   - **non tocca** altre regole firewall già presenti sul router (solo aggiunge le
     nuove, in cima alla chain corretta)

2. Interfaccia utente:
   - Pulsante "Genera script blocco accesso pubblico", visibile solo se
     `stato_connessione == connesso`
   - Warning esplicito prima di mostrare lo script: "esegui questo solo se hai già
     verificato che il tunnel VPN funziona, altrimenti rischi di perdere l'accesso al
     router"
   - Dopo l'esecuzione manuale da parte dell'utente, un pulsante "Conferma blocco
     applicato" che aggiorna un flag `accesso_pubblico_bloccato = True` sul router

3. Da questo punto in poi, tutte le fasi successive (backup, monitoraggio, terminale)
   devono usare **solo** `ip_vpn` per contattare il router, mai `ip_pubblico_o_ddns`.

## Criteri di completamento
- Su un router di test, dopo aver applicato lo script, l'API/SSH non risponde più
  dall'IP pubblico ma risponde regolarmente dall'IP VPN
- L'app aggiorna correttamente lo stato del router
- Nessuna funzionalità delle fasi precedenti si rompe

## Note
- Consigliare sempre all'utente di tenere una sessione WinBox/SSH aperta mentre applica
  lo script, come rete di sicurezza in caso di errore di configurazione
- Se emergono dubbi su come gestire un rollback automatico in caso di errore, annotalo
  in `fase_8_modifiche_rifinitura.md`
