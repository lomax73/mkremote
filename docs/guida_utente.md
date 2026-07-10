# MKRemote — Guida utente

Questa guida spiega come usare MKRemote da browser, passo per passo. Per la
documentazione tecnica di ogni fase del progetto vedi i file `fase_*.md` nella
radice del repository.

## Accesso

Vai all'indirizzo del server (es. `https://<ip-o-dominio-del-vps>/`) ed entra
con utente e password forniti dall'amministratore. Verrai reindirizzato alla
lista dei router.

---

## 1. Aggiungere un nuovo router

1. Dal menu laterale vai su **Router**.
2. Clicca **+ Nuovo router**.
3. Compila i campi:
   - **Nome**: identificativo univoco (es. `router-sede-milano`).
   - **Location**: descrizione libera del luogo (facoltativo).
   - **Note**: annotazioni libere (facoltativo).
   - **Modello hardware** / **Versione RouterOS**: facoltativi, utili come
     promemoria.
   - **IP pubblico o DDNS** (facoltativo): indirizzo con cui il router è
     raggiungibile da internet *prima* di collegarlo alla VPN (serve solo
     nella fase di configurazione iniziale). Può essere lasciato vuoto, ad
     esempio se il router è raggiungibile solo dalla rete locale finché non
     viene collegato alla VPN.
   - **IP LAN**: indirizzo del router nella rete locale, salvato come
     riferimento (es. per operazioni dirette in loco). Non viene usato per
     testare la connessione dall'app: il server dell'app gira sul VPS, quindi
     non ha accesso diretto alla rete locale del router — la verifica di
     connessione reale avviene via VPN (vedi punto 2 qui sotto).
   - **Porta SSH** (default 22) e **Porta API** (default 8728): porte del
     router usate per backup, monitoraggio e terminale.
   - **Username** e **Password**: credenziali di amministrazione del router.
     Sono salvate cifrate nel database, mai in chiaro. Accanto al campo
     Password c'è il pulsante **👁 Mostra password**, utile per rileggere
     quanto hai appena digitato prima di salvare — un secondo click la
     nasconde di nuovo. Per recuperare la password già salvata di un router
     esistente, vedi il punto successivo.
   - **Intervallo backup (ore)**: ogni quante ore eseguire il backup
     automatico (es. `24` per uno al giorno, `168` per uno a settimana). Se
     lasciato vuoto, restano solo i backup manuali.
   - **Numero backup da conservare**: quanti backup recenti tenere per questo
     router (i più vecchi vengono eliminati automaticamente).
4. Clicca **Salva**.

Il router compare ora nella lista con stato **Non configurato**: non è ancora
raggiungibile tramite VPN, va collegato (punto successivo).

Per modificare un router esistente, apri la sua scheda e clicca **Modifica**.
La password: se lasciata vuota in modifica, quella esistente **non viene
sovrascritta**.

**Recuperare la password di un router già salvato**: nella scheda di
dettaglio del router, alla riga **Password**, clicca **👁 Mostra password**.
L'app decifra e mostra la password effettivamente salvata (utile se l'hai
dimenticata); un secondo click la nasconde di nuovo.

Per rimuoverlo definitivamente, apri la scheda e clicca **Elimina** (azione
irreversibile: cancella anche lo storico di backup e metriche associate).

---

## 2. Collegare il router alla VPN

Prerequisito perché terminale, monitoraggio, backup e blocco dell'accesso
pubblico funzionino: il router deve avere un tunnel WireGuard attivo verso
l'hub.

1. Dalla scheda del router, clicca **Genera script VPN**.
2. Viene mostrato uno script RouterOS: copialo e incollalo in un terminale
   RouterOS (WinBox o SSH) del router. **Tieni aperta una sessione separata**
   di riserva (WinBox/SSH diretta) mentre lo esegui, come rete di sicurezza.
3. Lo script crea l'interfaccia WireGuard, genera la coppia di chiavi
   direttamente sul router (la chiave privata non lascia mai il router) e
   stampa la chiave pubblica generata.
4. Copia quella chiave pubblica nel campo **Chiave pubblica router** nella
   stessa pagina e clicca **Salva chiave**.
5. Clicca **Registra peer sul server**: l'app registra il router come peer
   sul VPS hub. Lo stato passa a **In attesa VPN**.
6. Clicca **Test connessione**: verifica che il router risponda sul suo IP
   VPN. Se ha successo, lo stato passa a **Connesso** e da qui in poi
   compaiono anche i pulsanti **Terminale** e **WebFig** nella scheda del
   router.
7. Clicca **Rileva caratteristiche dal router**: si collega al router sullo
   stesso IP VPN e ne legge modello hardware e versione RouterOS,
   aggiornando da sola quei due campi sulla scheda del router. Funziona solo
   dopo che il tunnel VPN è attivo (richiede lo stesso IP VPN del test
   connessione) e, oltre a compilare i dati, conferma anche che la
   connessione è effettivamente funzionante.

Se il test o il rilevamento falliscono, controlla che lo script sia stato eseguito
correttamente sul router e che il tunnel sia effettivamente attivo
(`/interface wireguard peers print` su RouterOS mostra un handshake recente).

---

## 3. Backup

Dalla scheda router, clicca **Backup** per accedere allo storico.

- **Backup manuale ora**: esegue subito un backup (RouterOS `.backup` +
  export `.rsc`), caricato sullo spazio FTPS configurato.
- I backup automatici, se è stato impostato un **Intervallo backup** in fase
  di creazione/modifica del router, partono da soli in base a
  quell'intervallo.
- Ogni riga della tabella mostra data, tipo, esito (**Riuscito**/**Fallito**,
  con il motivo in caso di errore) e dimensione.
- Se il backup è riuscito, è disponibile il link **Scarica** per recuperare
  il file.
- Solo gli ultimi N backup (il numero impostato in **Numero backup da
  conservare** sulla scheda router) vengono mantenuti: i più vecchi vengono
  eliminati automaticamente ad ogni nuovo backup riuscito.

---

## 4. Monitoraggio e alert

Dal menu laterale, **Monitoraggio**.

- **Dashboard**: vista d'insieme di tutti i router (stato, ultimo controllo,
  CPU e RAM correnti) e lista degli alert attualmente aperti.
- Cliccando su un router si apre la sua pagina di dettaglio con i grafici
  storici (CPU, RAM, temperatura) e l'elenco degli alert recenti (aperti e
  chiusi).
- I dati vengono raccolti automaticamente ogni pochi minuti da un processo in
  background (nessuna azione richiesta): non serve fare nulla perché le
  metriche si popolino, basta aspettare il primo ciclo dopo il collegamento
  del router alla VPN.
- **Impostazioni alert** (link nella dashboard) permette di configurare, senza
  bisogno di intervenire sul codice:
  - soglia CPU e soglia temperatura oltre le quali scatta un alert;
  - numero di controlli falliti consecutivi prima di marcare un router
    offline;
  - tempo minimo (cooldown) tra due notifiche ripetute dello stesso alert
    ancora aperto;
  - abilitazione e destinatario delle notifiche Telegram (serve un bot token
    configurato dall'amministratore) e/o email.

Gli alert vengono generati automaticamente per: router irraggiungibile,
CPU o temperatura sopra soglia, backup fallito. Si chiudono da soli quando la
condizione rientra (router di nuovo raggiungibile, CPU/temperatura tornate
normali, backup successivo riuscito).

---

## 5. Terminale nel browser e WebFig

Disponibili solo per router con stato **Connesso** (VPN attiva).

- **Terminale**: apre una sessione SSH direttamente nel browser verso il
  router, sulla sua rete VPN. Prima di iniziare va confermata esplicitamente
  l'apertura (è un accesso privilegiato) cliccando **Apri sessione
  terminale**. La sessione viene registrata per audit (chi, quando, su quale
  router). Per chiuderla: pulsante **Chiudi sessione**, oppure basta
  navigare via dalla pagina — la sessione si chiude comunque in automatico.
- **WebFig**: apre in una nuova scheda l'interfaccia web nativa di RouterOS,
  raggiungibile sull'IP VPN del router.

---

## 6. I miei dispositivi VPN personali

Dal menu laterale, **I miei dispositivi VPN**: permette di collegare i propri
dispositivi (telefono, laptop) alla stessa rete privata dei router, con un
solo profilo che raggiunge sia l'hub sia tutti i router già collegati.

1. Nel campo **Nome dispositivo**, scrivi un nome che ti aiuti a
   riconoscerlo (es. "iPhone di Mario"), poi clicca **Genera profilo**.
2. Viene mostrata una pagina **valida una sola volta**, con:
   - un **QR code** da inquadrare con l'app WireGuard ufficiale (iOS/Android)
     per importare il profilo in un tocco;
   - un link per scaricare il file `.conf` (utile su desktop, con l'app
     WireGuard per Windows/macOS/Linux).
3. Importa il profilo subito: la chiave privata generata **non viene mai
   salvata sul server**, quindi se chiudi questa pagina senza salvare il
   profilo altrove non è più recuperabile — in tal caso basta revocare il
   dispositivo (punto successivo) e crearne uno nuovo.
4. Una volta importato e attivato il tunnel sul dispositivo, dovresti riuscire
   a fare ping sia all'hub sia a qualunque router già collegato.

Per revocare l'accesso di un dispositivo (es. telefono perso o sostituito),
torna in **I miei dispositivi VPN** e clicca **Revoca** sulla riga
corrispondente: l'accesso viene disattivato immediatamente.

---

## Stati di un router, in sintesi

| Stato | Significato |
|---|---|
| Non configurato | Appena creato, VPN non ancora avviata |
| In attesa VPN | Peer registrato sul server, in attesa di conferma del tunnel |
| Connesso | VPN attiva e verificata: terminale, WebFig, backup e monitoraggio disponibili |
| Offline | Era connesso ma non risponde più (rilevato dal monitoraggio) |
