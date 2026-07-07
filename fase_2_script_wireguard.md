# Fase 2 — Generatore script WireGuard (hub-and-spoke)

## Obiettivo
Collegare ogni router al VPS tramite un tunnel WireGuard, con uno script generato
dall'app che l'utente copia e incolla nel terminale del router (via WinBox/SSH), senza
bisogno di installare nulla di esterno (WireGuard è nativo in RouterOS 7+).

## Prerequisiti
Fase 0 e Fase 1 terminate. Il VPS deve avere già un'interfaccia hub WireGuard (`wg0`) attiva.

## Architettura da implementare (hub-and-spoke)
- Tutti i router si collegano come peer del VPS su un'unica subnet privata (es. `10.10.0.0/24`)
- L'utente stesso avrà un profilo client sulla stessa subnet (vedi Fase 7), da un solo
  dispositivo raggiunge tutti i router
- La chiave privata di ogni router **non lascia mai il router**: viene generata
  direttamente lì dallo script, solo la chiave pubblica torna all'app

## Task da eseguire

1. Assegnazione IP:
   - Alla creazione/attivazione VPN di un router, l'app assegna il prossimo IP libero
     nella subnet (partendo da `.10` in su, vedi Fase 0)
   - Salvare l'IP assegnato nel campo `ip_vpn` del modello Router

2. Generatore script RouterOS (`.rsc`) da copiare/incollare, che deve:
   - generare la coppia di chiavi WireGuard localmente sul router
   - creare l'interfaccia `wireguard1` e assegnare l'IP privato assegnato dall'app
   - configurare il peer verso il VPS (IP pubblico del VPS, porta UDP, chiave pubblica
     del server — nota e fissa, salvata in config)
   - stampare a schermo la chiave pubblica generata (l'utente la copia manualmente
     nell'app)
   - **non modificare ancora il firewall** in questa fase (il blocco dell'accesso
     pubblico è la Fase 3, va fatto solo dopo aver verificato che il tunnel funziona)

3. Interfaccia utente:
   - Pulsante "Genera script VPN" nella vista dettaglio router → mostra lo script pronto
     da copiare (con syntax highlighting se possibile)
   - Campo dove incollare la chiave pubblica restituita dal router
   - Pulsante "Registra peer sul server": aggiunge il router come peer nella config
     WireGuard del VPS (usare `wg set` runtime + riscrittura persistente della config,
     poi `wg syncconf` per evitare downtime del tunnel esistente)
   - Pulsante "Test connessione": esegue un ping o una chiamata API minimale sull'IP
     VPN del router e aggiorna `stato_connessione` di conseguenza

## Criteri di completamento
- Su un router di test, eseguendo lo script generato, il tunnel si stabilisce
- Il test di connessione dall'app raggiunge il router sull'IP privato
- Aggiungere un secondo router non rompe il collegamento del primo (verifica esplicita)
- Nessuna chiave privata del router è mai transitata o salvata nel backend

## Note
- Documentare chiaramente nello script generato cosa fa ogni riga (commenti `:put` o
  `#`), utile per debug manuale futuro
- Se emergono dubbi su come gestire il rinnovo/rotazione delle chiavi, annotalo in
  `fase_8_modifiche_rifinitura.md`
