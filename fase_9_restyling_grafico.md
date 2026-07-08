# Fase 9 — Restyling grafico dell'interfaccia e pagina di login con logo

## Obiettivo
Dare all'interfaccia (dashboard e pagina di login) un aspetto curato e
riconoscibile, con un logo/branding dedicato, invece dello stile minimale
"funzionale" usato nelle fasi precedenti per non bloccare lo sviluppo.

## Prerequisiti
Nessun prerequisito funzionale stretto: può essere affrontata in qualsiasi
momento poiché tocca solo template/CSS, non la logica applicativa. Ha senso
farla quando le viste principali (Fasi 1-7) sono già stabili, per evitare di
restylare più volte le stesse pagine.

## Task da eseguire

1. Identità visiva:
   - Logo (fornito dall'utente o da creare) e favicon
   - Palette colori coerente (oggi i colori di stato — badge connesso/offline/
     ecc. — sono già scelti, vanno mantenuti come riferimento semantico)
   - Font/tipografia, eventualmente sostituendo il font di sistema attuale

2. Pagina di login (`templates/registration/login.html`):
   - Layout dedicato con logo, non più il form minimale attuale
   - Messaggi di errore più leggibili

3. Layout base (`templates/base.html`):
   - Header/nav con logo invece del solo testo "MKRemote"
   - Menu di navigazione più strutturato (oggi c'è solo link alla lista router
     e logout)
   - Revisione componenti condivisi: tabelle, badge di stato, pulsanti, form
     (oggi CSS minimale inline in `base.html`)

4. Responsive:
   - Verifica che dashboard e pagine di dettaglio siano usabili anche da
     schermi stretti (tablet/telefono), utile per interventi rapidi da mobile

## Criteri di completamento
- Pagina di login e dashboard hanno un aspetto coerente col logo/branding
  scelto, non più lo stile "grezzo" delle fasi precedenti
- Nessuna funzionalità delle fasi precedenti si rompe (form, badge di stato,
  pulsanti azione VPN/backup restano tutti funzionanti)
- L'interfaccia resta leggibile su schermi stretti

## Note
- Se non è ovvio quale libreria/approccio CSS usare (CSS scritto a mano come
  finora, vs un framework leggero tipo Tailwind/Bootstrap), annotalo come
  dubbio in `fase_8_modifiche_rifinitura.md` con pro/contro, ma scegli
  comunque un'opzione di default per non bloccare la fase.
- Se manca un logo pronto, annota in `fase_8_modifiche_rifinitura.md` la
  scelta adottata (placeholder testuale, logo generato, o richiesta esplicita
  del file all'utente) invece di bloccare la fase.
