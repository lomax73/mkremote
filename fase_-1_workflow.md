# Fase -1 — Workflow di esecuzione (leggere PRIMA di ogni fase)

Questo file non è una fase di sviluppo: è il protocollo che regola come tutte le altre fasi
(`fase_0_...md`, `fase_1_...md`, ecc.) devono essere eseguite. Vale per l'intero progetto.

## Regole obbligatorie per ogni fase

1. **Prima di iniziare una fase**, leggi il file `.md` corrispondente per intero e scrivi
   all'utente un riassunto in linguaggio semplice di:
   - cosa verrà creato/modificato in questa fase
   - quali file/moduli saranno toccati
   - eventuali decisioni tecniche che stai per prendere e perché
   - eventuali dubbi o alternative possibili

   **Aspetta conferma esplicita dell'utente prima di scrivere codice.**

2. **Appena l'utente conferma**, rinomina il file della fase aggiungendo il suffisso
   `_esecuzione` prima dell'estensione.
   Esempio: `fase_2_script_wireguard.md` → `fase_2_script_wireguard_esecuzione.md`

3. **Durante l'esecuzione**, se emerge un dubbio, una scelta non banale, o qualcosa che
   conviene rimandare (es. "andrebbe aggiunta la 2FA ma non è bloccante ora"), NON deciderlo
   autonomamente in modo definitivo: annotalo nel file `fase_8_modifiche_rifinitura.md`
   aggiungendo una voce nella sezione corretta (vedi quel file per il formato). Poi prosegui
   con l'implementazione della soluzione più semplice e ragionevole per non bloccare la fase.

4. **A fase completata e testata**, rinomina il file togliendo `_esecuzione` e aggiungendo
   `_terminato`.
   Esempio: `fase_2_script_wireguard_esecuzione.md` → `fase_2_script_wireguard_terminato.md`

5. **Non passare alla fase successiva** finché quella attuale non è `_terminato`, a meno che
   l'utente non chieda esplicitamente di procedere in parallelo.

6. **Se durante l'esecuzione alcune operazioni della fase vengono rimandate** (es. richiedono
   accesso a risorse non disponibili ora, come il VPS, o sono state esplicitamente rimandate
   dall'utente) e per questo la fase non può essere chiusa come `_terminato`, aggiungi anche il
   suffisso `_da_finire` al nome del file (mantenendo `_esecuzione`), per segnalare che il
   lavoro fatto finora non è completo e restano operazioni in sospeso.
   Esempio: `fase_0_fondamenta_esecuzione.md` → `fase_0_fondamenta_esecuzione_da_finire.md`
   Le operazioni rimandate vanno comunque annotate in `fase_8_modifiche_rifinitura.md` come da
   regola 3. Quando le operazioni in sospeso vengono completate, rimuovi `_esecuzione_da_finire`
   e applica la regola 4 (`_terminato`).

## Convenzione nomi file riassunta

| Stato                          | Nome file                                    |
|--------------------------------|-----------------------------------------------|
| Da iniziare                    | `fase_N_nome.md`                              |
| In corso                       | `fase_N_nome_esecuzione.md`                   |
| In corso con operazioni rimandate | `fase_N_nome_esecuzione_da_finire.md`      |
| Completata                     | `fase_N_nome_terminato.md`                    |

## Ordine delle fasi

`fase_0` → `fase_1` → `fase_2` → `fase_3` → `fase_4` → `fase_5` → `fase_6` → `fase_7`

`fase_8_modifiche_rifinitura.md` non segue questo ordine: è un file "vivo", aggiornato
in continuazione durante tutte le altre fasi, e viene affrontato per ultimo (o quando
l'utente lo richiede esplicitamente).
