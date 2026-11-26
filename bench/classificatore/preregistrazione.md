# Pre-registrazione · classificatore addestrato, sul modello dei detector seri

Scritta il 27/11/2026 prima di generare i testi gemelli, di scaricare il secondo campione web e il modello, e di addestrare.
Richiesta del proprietario: «come faccio a replicare i seri?», poi «Procediamo» sulla strada proposta (classificatore
italiano addestrato su coppie umano/generato, come esperimento in bench/ e non nella skill).

## Domanda
Un classificatore neurale addestrato in casa, con lo stesso principio di Pangram (coppie di testi umani e generati sullo
stesso tema), separa umano e generato meglio di detect.py, sugli stessi testi di verifica dell'indice, senza accusare
più persone?

## Uso
È una misura, non un bersaglio. Non si usa per guidare né per scegliere riscritture, e in questo giro non entra in
SKILL.md né nell'indice di affidabilità. Se regge, il proprietario decide se aggiungerlo a bench/ come strumento
opzionale (i pesi del modello non vanno nel repo).

## Dati di addestramento (solo sviluppo)
- Umani: primo campione web (mC4 2013-2020, 243 testi: blog 50, articoli 50, azienda 43, comunicati 50, servizi 50) e
  la metà di sviluppo del benchmark UD (prosa 101, social 121). In tutto 465.
- Generati: un gemello per ogni testo umano. Consegna: genere del testo, «circa N parole» (N = parole del testo umano),
  l'argomento dato dalle prime 20 parole del testo umano, come in taratura.py; nessun riferimento allo slop.
  Generi: blog «un articolo per un blog»; articoli «un articolo di notizie per un sito web»; azienda «la pagina "chi
  siamo" del sito di un'azienda»; comunicati «un comunicato stampa»; servizi «la pagina di un sito che descrive un servizio
  o un prodotto»; prosa «un brano in prosa, come in un articolo di giornale, una voce enciclopedica o un testo normativo,
  secondo l'argomento»; social «alcuni tweet, uno per riga».
- Generatori a rotazione, sugli id ordinati per genere: claude-haiku-5-5, gpt-6.2-sol, claude-sonnet-5-5, gpt-6-luna.
  Claude con `claude -p` in una cartella vuota senza impostazioni né strumenti; GPT con `codex exec --ignore-user-config
  --ephemeral --sandbox read-only` in una cartella vuota, ragionamento medium. Un tentativo in più se fallisce; se fallisce
  ancora la coppia si toglie e si riporta.
- Non usati: corpus_ia/dev (stesse consegne dei testi generati di verifica), testi accademici, tutto ciò che è di verifica.

## Dati di verifica (mai visti in addestramento)
Gli stessi dei 12 confronti dell'indice: umani UD test (prosa 101, social 121) e secondo campione web (shard 00001, 242
testi, riscaricato con bench/prepara_web.py, stessa selezione) contro quattro gruppi generati: Sonnet e Haiku di test
(30), GPT (60), Opus (30), Fable (30). Generatori Opus e Fable mai visti in addestramento; consegne dei testi generati
(post, email, landing page…) diverse da quelle dei gemelli.

## Modello e addestramento (fissati ora, nessuna messa a punto sui dati di verifica)
- dbmdz/bert-base-italian-xxl-cased (MIT), solo model.safetensors, con una testa di classificazione a due classi.
- Stessa normalizzazione per tutti i testi, umani e generati, in addestramento e in verifica: via la formattazione
  markdown (#, **, *, `, trattini d'elenco a inizio riga), spazi e a capo ridotti a uno spazio, apostrofi e virgolette
  curvi resi dritti. Lineette e altra punteggiatura restano. Serve a non far imparare la forma della pagina invece dello stile.
- Finestre di 256 token (al massimo 3 per testo, ognuna con l'etichetta del testo); in verifica la probabilità di un
  testo è la media delle sue finestre.
- 3 epoche, learning rate 2e-5, batch 8, weight decay 0,01, warmup 10%, seme 20261127. Validazione: 15% delle coppie
  (umano e gemello nella stessa parte), solo per controllare che l'addestramento funzioni; non si sceglie nulla su di essa.
- Confronto di base, riportato: TF-IDF su n-grammi di caratteri 2-5 con regressione logistica, stessi dati.

## Criteri
1. Riconoscimento: AUC media sui 12 confronti almeno pari a quella di detect.py sugli stessi testi (ricalcolata qui;
   nell'indice è circa 0,943), e nessun confronto sotto 0,85.
2. Falsi allarmi: con soglia 0,5 sulla probabilità, al massimo il 3% dei 464 testi umani di verifica giudicati generati
   (detect.py: 2,6% SEGNALATO).
- 1 e 2: REGGE. Solo 1: REGGE IN PARTE (riconosce, ma accusa troppe persone). Altrimenti: NON REGGE.

## Riportati senza criterio
AUC per confronto; quota dei 150 testi generati di verifica riconosciuti a soglia 0,5; AUC della combinazione con detect.py
(media dei ranghi); testi accademici (30 umani, 30 gemelli Claude: detect.py 0,52), fuori dominio; esito sulla validazione;
punteggio prima e dopo la riscrittura sulle letture alla cieca 1-6 (mediana per lettura); i due casi esterni (c03 della
prima lettura riscritto: Pangram IA 100%; o02 della sesta, originale e riscritto: GPTZero IA 100%).

## Limiti dichiarati prima
- Ordini di grandezza sotto Pangram: 930 testi contro milioni, 4 generatori contro 75, nessuna caccia ai propri errori.
- I gemelli nascono da consegne brevi; i testi umani di addestramento sono di genere diverso dai post dei testi di verifica.
- I testi umani UD hanno licenza non commerciale: non vanno nel repo, come i pesi.

## Correzione prima della corsa ufficiale (27/11/2026)
Fatta dopo una prova parziale richiesta dal proprietario («Facciamo una prova?»), che ha addestrato sui primi 142 gemelli
(solo generi web) e ha visto i numeri di verifica: AUC media 0,913, umani accusati 21,6%. La prova non conta. Le impostazioni
del modello e i criteri restano quelli scritti sopra; cambia solo la generazione dei gemelli, per due difetti:
- La consegna dei tweet diceva «alcuni tweet, uno per riga di circa N parole»: i modelli l'hanno letta come N parole per
  tweet, e i gemelli dei tweet sono venuti 3-4 volte più lunghi del testo umano (gli altri generi: 0,9-1,1). Contro
  l'intento scritto sopra (N = parole del testo umano). Nuova consegna: «Scrivi in italiano alcuni tweet, uno per riga,
  per circa N parole in tutto. L'argomento è quello di una serie di tweet che inizia così: «…». Rispondi solo con il
  testo, senza introduzioni né note.» I 121 gemelli dei tweet si rigenerano tutti, con gli stessi generatori.
- 10 risposte erano rifiuti di GPT (2 pagine aziendali, 8 serie di tweet), che il controllo sulle 15 parole non vedeva.
  Un rifiuto è una generazione fallita: si ritenta una volta e, se rifiuta ancora, la coppia esce (elenco in escluse.txt).

## Esito (27/11/2026) · REGGE IN PARTE
- Dati: 465 coppie (395 addestramento, 70 validazione), nessuna esclusa: i 4 rifiuti si sono risolti al secondo tentativo.
- Criterio 1, riconoscimento: AUC media sui 12 confronti 0,9905 contro 0,9428 di detect.py sugli stessi testi; minima
  0,963 (prosa contro Opus). SODDISFATTO. Confronto di base TF-IDF: 0,977.
- Criterio 2, falsi allarmi: con soglia 0,5, 32 testi umani su 464 giudicati generati (6,9%; criterio ≤ 3%). NON
  SODDISFATTO. Per gruppo: prosa 11/101, tweet 2/121, web 19/242. TF-IDF: 10,3%.
- Testi generati di verifica riconosciuti a 0,5: 149 su 150 (Sonnet e Haiku 30/30, GPT 60/60, Opus 29/30, Fable 30/30;
  Opus e Fable mai visti in addestramento).
- Combinazione con detect.py (media dei ranghi): 0,989, non meglio del classificatore da solo.
- Accademico, fuori dominio: AUC 0,999 (detect.py 0,52); 1 tesi umana su 30 sopra 0,5, 29 gemelli Claude su 30.
- Riscritture di umanizza, letture alla cieca 1-6: probabilità mediana 0,9995 prima e 0,9995 dopo in tutte e nove;
  nessun testo riscritto scende sotto 0,5.
- Casi esterni: c03 (originale e riscritto) e o02 (originale e riscritto) tutti a 0,999, come Pangram e GPTZero (IA 100%).
- Validazione: AUC 0,998; 6 umani su 70 sopra 0,5, nessun gemello sotto.
- Descrittivo, non previsto dai criteri: soglia 0,99 → 13 umani su 464 (2,8%) e 141 generati su 150. È scelta a
  posteriori: non vale come esito, serve a pre-registrare una prova futura.
- Testi umani accusati, a occhio: pagine commerciali e di marketing del web (servizi, cucine, cuffie, PEC), prosa
  formale e tradotta (economia, trattati UE, Wikipedia), due serie di tweet. È il profilo noto dei falsi positivi.
