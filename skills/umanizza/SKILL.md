---
name: umanizza
description: Humanizer per testi in italiano generati con l'IA. Toglie lo slop dai testi scritti con l'IA (post, caption, newsletter, email, articoli) con due script che girano davvero - humanize.py pulisce invisibili, tipografia e le voci sicure di un lessico italiano di 239 voci; detect.py dà un punteggio su cinque controlli e il delta prima/dopo. Poi riscrive a mano ciò che richiede giudizio (non è solo X è Y, triadi, chiuse che chiedono commenti, Title Case all'inglese). Usare quando l'utente chiede di togliere lo slop, umanizzare, rendere meno da ChatGPT, rendere più naturale o più umano un testo in italiano, controllare se un testo sembra scritto dall'IA, o invoca /umanizza. Anche per tararla sui post social dell'utente (taratura personale). Anche per bozze proprie da rifinire prima di pubblicarle. Non per testi in altre lingue.
---

# umanizza

Toglie le sbavature che lasciano i modelli quando scrivono in italiano. Due script locali, senza dipendenze e senza rete, più un passaggio di riscrittura che solo tu puoi fare bene.

File in questa cartella:

- `humanize.py`: pulizia meccanica in tre passate (invisibili, tipografia, lessico)
- `detect.py`: punteggio su cinque controlli, confronto prima/dopo
- `lessico.py`: il motore condiviso
- `slop.json`: lessico, caratteri invisibili, tell strutturali. Si modifica a mano.
- `voce-modello.md`: il modello per il file della voce dell'utente
- `taratura.py`: tara le soglie sui post social dell'utente (vedi "Taratura sui tuoi social")
- `prima-di-scrivere.md`: il brief da leggere prima di scrivere un testo nuovo (vedi "Prima di scrivere")
- `docx.py`: file Word; estrae il testo e applica modifiche come revisioni tracciate, con verifiche (vedi "File Word")

Chiama gli script con il percorso di questa cartella, per esempio `python3 <cartella-skill>/detect.py`.

## Prima di tutto: la voce

Se esiste `~/.claude/umanizza/voce.md`, leggilo e rispettalo in ogni riscrittura: è il modo in cui scrive l'utente. Se non esiste, lavora comunque e alla fine offri in una riga di crearlo (da `voce-modello.md` in questa cartella, oppure dall'analisi di tre testi che l'utente ha scritto davvero).

## Prima di scrivere

Quando l'utente ti chiede di scrivere un testo nuovo in italiano, e non di correggerne uno, leggi prima `prima-di-scrivere.md` in questa cartella e applicalo mentre scrivi; poi segui il flusso qui sotto. Il brief non toglie il watermark di Claude e non garantisce nulla sui detector.

## Flusso

1. **Salva la bozza** in un file di lavoro (`bozza.txt`). Non toccare l'originale dell'utente.
2. **Misura**: `python3 detect.py bozza.txt --dettagli`. Tieni il punteggio di partenza.
3. **Pulizia meccanica**: `python3 humanize.py bozza.txt --report -o pulito.txt`. Il report elenca cosa ha cambiato e cosa resta da riscrivere a mano.
4. **Riscrivi** `pulito.txt` partendo dalla sezione "DA RISCRIVERE A MANO" del report, con le regole qui sotto. Salva in `riscritto.txt`. Se chi firma il testo vuole rivederlo da sé (in una tesi deve farlo), non riscrivere tu: consegnagli il report, dove ogni segnalazione ha una domanda (`?`), e la mappa delle frasi (`detect.py --mappa`); dopo la sua revisione applichi solo la pulizia meccanica.
5. **Verifica**: `python3 humanize.py riscritto.txt -o riscritto.txt` per ripulire quello che la riscrittura ha reintrodotto, poi `python3 detect.py bozza.txt riscritto.txt`. Il confronto stampa anche FEDELTÀ: rimetti i numeri, i nomi e i virgolettati spariti, controlla quelli comparsi (non devono essere inventati); oltre il 30% di parole cambiate rileggi tutto, oltre il 50% fermati e chiedi a chi firma il testo.
6. Se il verdetto non è PASSA e restano segnalazioni che si possono sistemare senza snaturare il testo, torna al punto 4. Massimo tre giri: se dopo tre giri il punteggio è sotto 85, consegna comunque e di' quale controllo resta basso e perché. PASSA è il criterio per fermarsi, non lo scopo: non riscrivere una frase solo per alzare il punteggio.

## Regole della riscrittura

- **Togli prima di sostituire.** La maggior parte dello slop non va riformulata: va cancellata. "È importante sottolineare che X" diventa "X".
- **Concreto al posto di generico.** Numeri, nomi, strumenti, date, quanto tempo, quanto costa. CONCRETEZZA è il controllo che separa di più i testi umani da quelli generati.
- **Non inventare mai.** Niente numeri, clienti, risultati o aneddoti che l'utente non ti ha dato. Se serve un dato che non hai, scrivi `{{il tuo numero}}`, `{{nome cliente}}` e così via, e alla fine elenca i segnaposto da riempire. Un testo con un segnaposto è meglio di un testo con un fatto falso.
- **Smonta le strutture, non solo le parole:**
  - *Non è solo X, è Y* / *Non si tratta di X, ma di Y* / *Non X, ma Y*: di' Y e basta.
  - *Il risultato? ...* / *La verità è una:*: togli la domanda, tieni la risposta.
  - Triadi in raffica ("veloce, semplice e sicuro"): tieni l'elemento che conta, o dai un esempio al posto dell'elenco.
  - *Più X, più Y*, *Primo/Secondo/Terzo*: solo se il contenuto è davvero una sequenza.
  - Chiusa che chiede commenti ("E voi? Ditemelo nei commenti"): toglila, a meno che l'utente non voglia esplicitamente una call to action. In quel caso una sola, specifica.
  - Title Case all'inglese nei titoli: in italiano solo la prima parola e i nomi propri.
  - Elenchi con emoji in testa a ogni riga: prosa, o un elenco semplice.
- **Varia il ritmo.** Una frase corta dopo una lunga. Non tutte da 15 parole.
- **Cosa fa da solo `humanize.py`:** solo 42 sostituzioni che non cambiano il senso, e cancellazioni solo a inizio frase o tra due virgole. Tutto il resto (aggettivi, "tuttavia", "un vero e proprio", "a 360 gradi") lo segnala: decidi tu in base al contesto, perché in senso tecnico o letterale molte di quelle parole vanno bene.
- **Mantieni il significato e il registro.** Un testo formale resta formale: umanizza toglie lo slop, non trasforma una circolare in un post.
- **Non introdurre nuovi tell** mentre ne togli altri. Per questo il punto 5 rilancia gli script.
- **Lineetta di dialogo** a inizio riga è italiano corretto: resta.
- **Un segnale debole da solo non si tocca.** Una voce o un tell segnalati come deboli contano solo se nello stesso paragrafo ce ne sono altri; isolati, sono il modo normale in cui scrive una persona.
- **Quando non intervenire:** citazioni e virgolettati (sono parole di altri), testi scritti prima di fine 2022 (non possono venire da un modello), formule fisse delle lettere (saluti, firme), chat informali tra persone, nomi propri e titoli di opere. Idea ripresa da blader/humanizer (licenza MIT).

## Cosa consegnare

1. Il testo finale in un blocco pronto da copiare.
2. Il delta, in una riga per controllo, preso dall'output di `detect.py prima dopo`.
3. I segnaposto `{{...}}` da riempire, se ce ne sono.
4. Se è rimasto qualcosa di segnalato apposta (per esempio una CTA voluta), dillo in una riga.

Non pubblicare niente: l'utente copia e pubblica.

## Modalità ridotte

- "Controlla solo" / "sembra scritto dall'IA?": solo il punto 2, poi spiega in tre righe i controlli più bassi e le voci trovate.
- "Pulizia veloce" / "solo i caratteri invisibili": solo `humanize.py --solo invisibili,tipografia`.
- Testi lunghi (oltre 1.500 parole): lavora per sezioni e misura ogni sezione.

## Modalità accademica (tesi, articoli, saggi)

- `detect.py --genere accademico` e `humanize.py --genere accademico`: citazioni autore-anno, rimandi di pagina e richiami di nota non contano in CONCRETEZZA, e gli elenchi di nomi, opere e date non vengono segnalati come triadi. **Sui testi accademici il verdetto non distingue Claude dalle persone**: nella misura del 23/11/2026 (30 estratti di tesi e articoli umani precedenti al 2022 contro 30 gemelli di Claude sugli stessi temi) l'AUC del punteggio è 0,52, il 57% dei testi umani passa e così il 53% di quelli di Claude. SLOP e RITMO vanno al contrario (AUC 0,13 e 0,37: gli umani usano più «inoltre» e «tuttavia», Claude varia di più la lunghezza delle frasi); separano un poco solo CONCRETEZZA (0,63) e VOCE (0,62). Dillo all'utente: in una tesi contano le segnalazioni, la fedeltà e la sua lettura, non il numero.
- `detect.py --mappa`: le frasi da riscrivere a mano per prime, con il motivo (gerundio dopo la virgola, nominalizzazioni, connettivo in apertura, «È importante che») e una domanda per chi scrive. Non entra nel punteggio e non è validata: nella misura del 23/11/2026 (30 testi di Claude contro 222 testi umani del banco, generi diversi da una tesi) solo le nominalizzazioni separano Claude dagli umani (AUC 0,70); gerundi, connettivi in apertura e impersonali no (AUC 0,48-0,51). Sui testi accademici gerundi dopo la virgola e connettivi in apertura sono anzi più frequenti negli umani (AUC 0,31 e 0,39), e le nominalizzazioni separano ancora un poco (0,62). In una tesi guarda solo le frasi segnalate per le nominalizzazioni, come promemoria di lettura e non come prova.
- Le frasi in cima alla mappa le riscrive chi firma il testo, non Claude: nelle prove è l'unica revisione che sposta anche i detector forti senza alterare i fatti. Claude applica solo la pulizia meccanica e controlla che numeri, nomi, date e citazioni non siano cambiati.
- In una tesi l'uso dell'IA va dichiarato secondo le regole dell'ateneo: ricordalo in una riga, una volta.

## File Word (.docx): revisione con un piccolo council

Su un file Word non far mai passare `humanize.py` sul documento: le modifiche si decidono sul testo e si applicano come revisioni tracciate, che l'utente accetta o rifiuta una per una in Word.

1. **Estrai e misura**: `python3 docx.py estrai file.docx --note -o testo.txt`, poi `detect.py` (con `--genere accademico` per tesi e articoli) e `humanize.py testo.txt --report` per le segnalazioni.
2. **Piccolo council, due revisori indipendenti.** Avvia due revisori nuovi che leggono solo `testo.txt` (più `voce.md`, se c'è) e non vedono il lavoro dell'altro: meglio uno Claude (subagente) e uno Codex (`codex exec --sandbox read-only` in una cartella che contiene solo il testo e il brief), altrimenti due subagenti Claude. Il brief contiene le "Regole della riscrittura" e chiede una lista nel formato di `modifiche.json` (`id`, `vecchio`, `nuovo`, più `perche`): togliere prima di sostituire, nessun fatto nuovo, citazioni e virgolettati intatti, registro invariato.
3. **Sintesi (la fai tu, che coordini):**
   - tieni le modifiche proposte da entrambi i revisori;
   - di quelle proposte da uno solo, tieni solo quelle che rispondono a una regola esplicita (un tell, una ripetizione, un'incoerenza interna), dopo averle controllate;
   - scarta tutto ciò che tocca numeri, date, nomi, citazioni o le posizioni dell'autore (cautele, giudizi): diventano domande per l'utente.
4. **Applica**: `python3 docx.py applica file.docx modifiche.json -o file_revisioni.docx`, poi lo stesso con `--accettate -o file_pulito.docx`. Esce con 1 se una modifica non si applica (testo non trovato o non unico): correggi `vecchio` e rilancia. Leggi le avvertenze: note la cui frase è cambiata, numeri, nomi e virgolettati spariti o comparsi.
5. **Terzo sguardo (consigliato)**: un revisore nuovo legge la versione pulita e segnala solo i problemi introdotti dalla revisione (frasi monche, note fuori posto, promemoria rimasti, ripetizioni nuove). Così il 23/11 sono emersi un promemoria lasciato in una nota e un richiamo finito sulla frase sbagliata.
6. **Consegna**: il file con le revisioni tracciate (autore «umanizza»), quello pulito, e le modifiche scartate come domande per l'utente.

È una revisione fatta da modelli: migliora il testo, non lo rende scritto da una persona e non sposta i detector forti. Non ripeterla per abbassare il punteggio di un detector; in una tesi va dichiarata. Le chiamate a Codex usano l'abbonamento collegato: se fosse una chiave a pagamento, chiedi prima all'utente.

## Taratura sui tuoi social

Quando l'utente chiede di tarare umanizza, di "misurarla sui miei post", o la usa spesso su una piattaforma: `taratura.py` confronta i suoi post con quelli di Claude sugli stessi argomenti e salva soglie personali in `~/.claude/umanizza/taratura.json`. Da lì `detect.py` le usa da solo (`--generico` per ignorarle, `--piattaforma threads` per quelle di un social).

1. **Export.** Chiedi all'utente gli export dei social che usa. Il percorso esatto nei menu cambia spesso: indica solo dove cercare e lascia che sia l'utente a trovarlo.
   - Threads, Instagram, Facebook: Centro gestione account di Meta, "Scarica le tue informazioni", formato **JSON**.
   - LinkedIn: impostazioni privacy, copia dei dati; serve `Shares.csv`.
   - X: archivio dei dati; serve `tweets.js`.
   - Qualsiasi altro social: una cartella con un post per file `.txt`, chiamata come il social.
2. **Importa:** `python3 taratura.py importa EXPORT... --cartella tara/`. Se l'utente ha scritto alcuni post con l'IA, aggiungi `--prima-di 2022-11-30`, oppure fagli togliere a mano quei file da `tara/umano/`: un post scritto con Claude nel gruppo umano falsa la misura.
3. **Gemelli.** Se c'è `ANTHROPIC_API_KEY`: `python3 taratura.py genera tara/`. Se non c'è, scrivili tu da `tara/consegne.jsonl`, uno per consegna, in `tara/ia/<piattaforma>/<id>_claude.txt`. Vanno scritti come li scriveresti normalmente, **senza** applicare le regole di questa skill: il punto è misurare Claude così com'è. Se puoi, affida ogni consegna a un subagente nuovo, che non ha visto queste istruzioni.
4. **Misura:** `python3 taratura.py misura tara/`. Riporta all'utente l'AUC e la quota di coppie vinte per piattaforma, e quali controlli separano di più.
5. **Applica:** `python3 taratura.py applica tara/`. Le soglie personali possono solo abbassarsi rispetto a quelle generiche (85/70): servono a non segnalare il modo di scrivere dell'utente, non a essere più severe.
6. Servono almeno 20 post per tarare e 30 per piattaforma perché la misura regga: dillo se sono meno.

## Senza Python

Se non puoi eseguire script (per esempio in una chat senza strumenti), leggi `slop.json` e applica a mano le stesse tre passate e le regole di riscrittura. Di' all'utente che il punteggio non è stato calcolato.

## Cosa significa il punteggio

- **PASSA** (85 o più), **DUBBIO** (70-85), **SEGNALATO** (sotto 70). Soglie tarate su 222 testi umani italiani scritti prima dei modelli linguistici e 30 generati.
- Se esiste una taratura personale, `detect.py` lo scrive nella prima riga e usa quelle soglie.
- **N/D** sotto le 15 parole o se il testo non sembra italiano: in quel caso non dare un verdetto.
- È tarato su testi in italiano generati da Claude Sonnet e Haiku e verificato su Claude Opus e Fable (AUC in prosa 0,94) e su GPT (0,90). Su Gemini e altri modelli le soglie non sono state misurate: dillo all'utente se il testo viene da lì.
- È una misura di quanto il testo *si legge* come generato, non una prova di chi l'ha scritto. Testi burocratici umani possono finire in DUBBIO; testi generati e poi riscritti bene finiscono in PASSA, ed è lo scopo.
- Non è GPTZero né un altro detector commerciale e non li chiama. Non promettere a nessuno che il testo "non verrà rilevato".
- I caratteri invisibili a larghezza zero limitano il punteggio a 60 finché ci sono: nessuna tastiera li produce.
