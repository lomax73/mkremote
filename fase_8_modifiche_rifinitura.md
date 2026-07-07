# Fase 8 — Modifiche e rifinitura

## Cos'è questo file
A differenza delle altre fasi, questo file **non ha un obiettivo unico e non segue
l'ordine numerico**. È un contenitore vivo, aggiornato in continuazione durante tutte
le altre fasi (vedi `fase_-1_workflow.md`, regola 3).

Ogni volta che durante una fase emerge:
- un dubbio tecnico non banale
- una scelta con più alternative valide
- una funzionalità utile ma non bloccante da rimandare

...va annotata qui invece di essere decisa in modo definitivo e silenzioso durante lo
sviluppo della fase corrente.

## Formato di una voce

Per ogni voce aggiunta, usare questo schema minimo:

```
### [Fase di origine] Titolo breve del dubbio/rimando
- Contesto: perché è emerso
- Opzioni valutate: elenco alternative con pro/contro
- Scelta di default adottata (se presa per non bloccare la fase): quale e perché
- Stato: da decidere / rimandato / risolto
```

## Rifiniture note già previste da subito

Queste sono rifiniture individuate in fase di progettazione iniziale, da affrontare
qui quando le fasi 0-7 sono stabili:

### [Generale] Autenticazione a due fattori (2FA) sul login dashboard
- Stato: da decidere (quale libreria/metodo: TOTP standard consigliato)

### [Generale] Audit log
- Traccia di chi ha fatto cosa e quando (creazione/modifica router, esecuzione
  backup manuale, apertura terminale, modifiche a soglie di alert)
- Stato: da decidere

### [Generale] Ruoli utente
- Da valutare solo se in futuro l'accesso alla dashboard viene condiviso con
  collaboratori (oggi non è un requisito, uso singolo utente)
- Stato: rimandato, non necessario allo stato attuale

---

## Voci aggiunte durante lo sviluppo

*(Claude Code aggiunge qui le nuove voci man mano che emergono durante le fasi 0-7,
seguendo il formato sopra)*
