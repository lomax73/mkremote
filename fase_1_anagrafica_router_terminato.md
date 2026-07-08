# Fase 1 — Anagrafica router (CRUD base)

## Obiettivo
Avere un'interfaccia funzionante per registrare, consultare, modificare ed eliminare i
router Mikrotik in gestione, con le credenziali salvate in modo sicuro.

## Prerequisiti
Fase 0 terminata (progetto Django + DB funzionanti).

## Task da eseguire

1. Modello `Router` (app `routers`) con almeno questi campi:
   - `nome`, `location`, `note` (testo libero)
   - `modello_hardware`, `versione_routeros`
   - `ip_pubblico_o_ddns`, `porta_ssh`, `porta_api`
   - `username` e `password` cifrati a riposo (usare libreria di cifratura simmetrica,
     chiave master letta da env, mai in chiaro nel DB né nel codice)
   - `ip_vpn` (nullable finché non collegato via WireGuard — vedi Fase 2)
   - `chiave_pubblica_wireguard` (nullable)
   - `stato_connessione`: enum tipo `non_configurato / in_attesa_vpn / connesso / offline`
   - `intervallo_backup` (usato dalla Fase 4, ma il campo va previsto già ora)
   - timestamp creazione/modifica

2. CRUD completo:
   - Vista lista router con stato connessione a colpo d'occhio (badge colorato)
   - Form creazione/modifica (validazione IP, porte, campi obbligatori)
   - Vista dettaglio router con tutte le informazioni
   - Eliminazione con conferma

3. Autenticazione base:
   - Login richiesto per accedere alla dashboard (usare l'auth di Django, poi rifinire
     in Fase 8 se serve 2FA)

4. Decidere e documentare (in un semplice README o commento) l'interfaccia scelta:
   - Django templates classiche + qualche JS leggero (htmx/Alpine.js), oppure
   - API DRF + frontend separato (React/Vue)

   Se non è ovvio quale sia la scelta migliore, annotalo come dubbio in
   `fase_8_modifiche_rifinitura.md` con pro/contro, ma scegli comunque un'opzione di default
   per non bloccare la fase (consigliato: Django templates + htmx, più semplice da mantenere
   in solitaria).

## Criteri di completamento
- Posso aggiungere un router con tutti i suoi dati e vederlo salvato cifrato nel DB
- Posso modificarlo ed eliminarlo
- La password non è mai visibile in chiaro nell'interfaccia (solo in fase di edit, mascherata)
- Login obbligatorio per accedere a qualunque vista

## Note
Questa fase non fa ancora nessuna connessione reale al router: è pura anagrafica.
La connessione vera arriva in Fase 2.
