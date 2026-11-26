# Changelog

Cosa è cambiato dopo aver visto i dati, in ordine. Serve a verificare il README: cosa è stato tarato e su quali dati.

## 1.6.0 · 26 novembre 2026

- **README per il lancio**: il resoconto completo delle prove passa in `docs/validazione.md`; nel README restano il riassunto, l'indice, la formula e i limiti. Descrizioni di skill, plugin e repo senza l'elenco dei modelli.
- **IMPRONTA corretto**, con criteri fissati prima di scaricare i dati di verifica. Diagnosi sul primo campione web: le lineette come inciso compaiono nel 28% dei testi umani e in 1 testo generato su 90, quindi pesavano contro le persone (AUC 0,35). Ora sono riportate ma non tolgono punti; gli invisibili restano. Verifica su un secondo campione web mai usato (242 testi, shard 00001, nessuna pagina in comune): IMPRONTA da 0,354 a 0,481 (soglia 0,48), totale contro GPT da 0,890 a 0,896, testi umani con PASSA da 83,1% a 83,9%. Benchmark invariato.
- `bench/prepara_web.py --shard N` per scegliere il file di validazione; risultati del secondo campione in `bench/risultati/web2_*.json`; tutti i risultati ricalcolati con la 1.6.0. La bozza d'esempio passa da 20,8 a 21,8 (sempre SEGNALATO).
- **Modelli Claude più forti**, con criteri fissati prima: le 30 consegne scritte da Claude Opus 5.5 e Fable 5.2 (60 testi, `bench/corpus_claude_forti/`), ognuno da una sessione isolata. Prosa 0,936 e 0,941, tweet 0,993 e 0,992, web 0,933 e 0,934: si riconoscono meglio di Sonnet e Haiku. Risultati in `bench/risultati/opus*.json` e `fable*.json`.
- **Copertina** in stile taccuino di Leonardo (`docs/copertina.jpg`, sorgente SVG). Grafici con le barre di Opus e Fable ed etichette «Sonnet e Haiku» al posto di «Claude».
- **Indice di affidabilità** da 0 a 10, calcolato da `bench/indice.py` sui soli dati di verifica con una formula fissata prima del calcolo (riconoscimento, falsi allarmi, copertura dei generi, pulizia, fedeltà, leggibilità): 7,88. Nuovi `bench/risultati/pulizia.json` (9 sostituzioni su 444 testi umani, ricontrollate: 0 sbagliate) e `accademico.json`.
- **Terza lettura alla cieca**, con criteri fissati prima e la condizione del proprietario («se la media dei due peggiora non applicarla»): regole nuove di riscrittura (tenere i legami, rispettare il genere, non appiattire) su 20 testi nuovi. Claude migliora (preferito 9 e 10 su 10), Codex peggiora (0 e 4 su 10), media incrociata 10/20 contro 12/20: regole non applicate, `SKILL.md` invariato. Materiali in `bench/lettura-cieca-3/`.
- README: perché un indice di 10 è impossibile e cosa può alzarlo davvero.
- **Quarta lettura alla cieca**, con criteri fissati prima: riscrittura a modifiche puntuali (`modifiche.py`) con verifica alla cieca di ogni modifica, più le regole della terza prova. Codex migliora (5 e 8 su 10), Claude cala (7,5 e 6), media incrociata 11/20 contro 12/20: non applicata. La versione sperimentale resta in `bench/lettura-cieca-4/skill-sperimentale/`.
- **Copertina nuova**: spaccato in stile Leonardo di un'entità astratta divisa in strati, titolo in gotico, scritte allo specchio, la formula del punteggio annotata a mano. **README**: sezione «La formula» con le formule dei cinque controlli.
- 4 test nuovi (119 in tutto), tra cui uno che controlla che l'indice nel README sia quello calcolato.
- **Classificatore addestrato** (`bench/classificatore/`), con criteri fissati prima: un BERT italiano addestrato su 465 testi umani e 465 gemelli generati, sul modello dei detector commerciali. Sui 12 confronti dell'indice AUC 0,991 contro 0,943 di `detect.py`, ma 6,9% di testi umani accusati (criterio 3%): regge in parte. Prova di conferma a soglia 0,99 su testi nuovi: 48 generati su 50 riconosciuti, 15 umani su 262 accusati (5,7%): non regge. La riscrittura di umanizza non sposta il suo punteggio. Sugli stessi testi nuovi SEGNALATO accusa 6 umani su 262 e nessun brano di prosa formale. Pesi del modello, testi umani e gemelli dei testi UD non sono nel repo.
- **README**: «Un 10 è impossibile», con la misura che lo mostra; sezione nuova «Limiti dei detector», con la soglia di umanizza confrontata con quella del classificatore; riga «I detector esterni sono affidabili?» nella tabella iniziale. Grafico nuovo `docs/grafici/soglie-*.svg` (da `bench/grafici.py`): persone accusate e testi generati presi per soglia, sugli stessi testi nuovi. `docs/validazione.md`: classificatore, conferma, confronto delle soglie e limiti dei detector dalla letteratura.
- **Tre prove che non hanno retto**, tutte con criteri fissati prima e riscrittore Claude; `SKILL.md` e indice invariati. Braccio 4b (Claude riscrive testi di GPT): 5 e 6 su 10, incerto. Quinta prova («riscrive solo Claude», 20 testi, due regole): 18 e 21,5 su 40 contro una soglia di 25; sui testi di GPT i lettori preferiscono l'originale (5 e 8,5 su 20). Sesta prova (riscrittura guidata da un profilo di genere ricavato da testi web umani, 20 testi di Opus e Fable): 19 su 40 contro 28,5 della skill così com'è. Materiali in `bench/lettura-cieca-4b/`, `-5/` e `-6/`.
- **Detector esterni, due casi**: una riscrittura con `detect.py` a 86,0 (PASSA) è «IA al 100%» per Pangram 4.1; un'altra a 87,2 (PASSA) è «IA al 100%» per GPTZero, come il suo originale. README: «Serve a superare i detector esterni?» passa da «Non è lo scopo» a «No»; «Il testo riscritto si legge meglio?» da «Con Claude sì» a «Non sempre», con gli intervalli delle sei prove; nuovo limite «PASSA non vuol dire non rilevabile».
- **Due correzioni dalla revisione indipendente** (braccio 4b: Claude che riscrive testi GPT, incerto, 5 e 6 su 10): `humanize.py` non trasforma più in virgola la lineetta dopo luogo e data in apertura di un comunicato («[Città], [data] — …»); il controllo di fedeltà non dà più per persa una citazione quando cambia solo l'apostrofo o la virgoletta, da curva a dritta. Sui 625 testi del benchmark la pulizia cambia solo in 3 intestazioni di comunicati. 5 test nuovi (124 in tutto).

## 1.5.0 · 26 novembre 2026

- **Confronto a parità di genere**, con criteri fissati prima di scaricare i dati: 243 testi web italiani del 2013-2020 (mC4, `allenai/c4`), selezionati in automatico per genere dall'URL (blog, articoli, pagine aziendali, comunicati, servizi). AUC contro GPT 0,904 (criterio ≥ 0,80), contro Claude 0,919; per genere 0,89-0,91. Testi web: 87% PASSA, 10% DUBBIO, 3% SEGNALATO. `bench/prepara_web.py` scarica e rifà la selezione; risultati in `bench/risultati/web_*.json`. Lessico, pesi e soglie invariati.
- Osservazione da verificare su dati nuovi: IMPRONTA va al contrario sui testi web (AUC 0,35).
- Grafici: due barre (web contro Claude e GPT) e una riga di verdetti per i testi web. 3 test nuovi per la selezione.

## 1.4.2 · 26 novembre 2026

- **Seconda lettura alla cieca**, con criteri fissati prima: `SKILL.md` reso più restrittivo (riscrivere solo le frasi segnalate, sotto il 30% di parole cambiate) e prova ripetuta su 20 testi nuovi. Codex scende dal 43% al 14% di parole cambiate ma le sue riscritture sono preferite in 3 coppie su 10 (criterio di successo: 7). Claude resta a 7,5 su 10 ma l'aspetto umano cala (incrociato 11,5/20 contro 16,5/20). Ipotesi smentita: la modifica a `SKILL.md` è tolta. Materiali in `bench/lettura-cieca-2/`.
- README: in Codex conviene usare umanizza per misurare e pulire e lasciare la riscrittura a Claude Code; tabella «In breve» aggiornata.

## 1.4.1 · 26 novembre 2026

- **Lettura alla cieca** della riscrittura, con criteri fissati prima: 20 testi (10 Claude, 10 GPT) riscritti con umanizza da Claude e da Codex, 20 coppie giudicate senza sapere quale testo fosse l'originale da un agente Claude e da GPT. Giudizio incrociato: si legge meglio 12/20 (incerto, soglia 14), sembra di una persona 16,5/20. Riscritture di Claude preferite 8/10 da entrambi; di Codex 4-5/10. Nessun fatto perso o aggiunto. Materiali in `bench/lettura-cieca/`.
- README: la tabella «In breve» riporta questi risultati al posto di «da misurare».

## 1.4.0 · 26 novembre 2026

- **Verifica su GPT**, con criteri fissati prima della generazione: le 30 consegne del benchmark scritte da gpt-6.2-sol e gpt-6-luna tramite Codex CLI (60 testi, `bench/corpus_gpt/`, risultati in `bench/risultati/gpt.json`). AUC in prosa 0,898 (Claude 0,905), tweet 0,978 (Claude 0,986); verdetti GPT 13% PASSA, 48% DUBBIO, 38% SEGNALATO. Criterio (prosa ≥ 0,85) soddisfatto. Lessico, pesi e soglie invariati.
- **Codex**: la skill funziona da `~/.codex/skills/umanizza` (provato con Codex CLI 0.172: carica `SKILL.md`, esegue `detect.py` e `humanize.py`, riscrive e confronta). Istruzioni di installazione nel README.
- **Grafici** nel README (AUC per gruppo, verdetti, prima/dopo), in SVG chiaro e scuro, rigenerabili con `bench/grafici.py` dai risultati.
- **Revisione di SLOP**, con criteri fissati prima: 16 voci che nei testi umani di sviluppo compaiono almeno quanto in Claude («inoltre», «tuttavia», «pertanto», «qualora»…) hanno `"slop": false` e non contano più nel punteggio; `humanize.py` le segnala e sostituisce come prima (0 differenze su 565 testi). Verifica sui testi GPT: AUC di SLOP in prosa da 0,540 a 0,601, totale da 0,898 a 0,904; prosa umana con PASSA da 80,2% a 82,2%. Claude test (terzo giro): prosa da 0,905 a 0,911. Lessico 1.4.0. Pesi e soglie invariati.
- README: la skill è dichiarata per Claude Code e Codex (prima diceva solo Claude), anche nel flusso, nel profilo di voce e nella taratura.
- **GitHub Actions**: test su Python 3.9-3.13 a ogni push, più il controllo dei verdetti degli esempi del README.
- Descrizioni aggiornate: «tarato su Claude, verificato su GPT». 6 test nuovi (grafici e revisione di SLOP), 112 in tutto.

## 1.3.1 · 26 novembre 2026

- Prima versione pubblica. README riscritto: installazione (plugin, copia manuale, claude.ai), funzionamento, validazione, limiti.
- Descrizioni di skill, plugin e marketplace riformulate («per testi in italiano generati con l'IA»). Aggiunta la descrizione del marketplace.
- Esempi dei test resi neutri (nomi e titoli inventati). Codice, lessico, punteggi e benchmark invariati; 106 test.
- Misurata e scartata una correzione di SLOP in modalità accademica (ignorare le voci deboli di connettivo e burocratese): sulle coppie di verifica l'AUC di SLOP sale da 0,14 a 0,29, sotto la soglia di 0,40 fissata prima del test. Non inclusa.

## 1.3.0 · 23 novembre 2026

- **`docx.py`**, file Word in sola libreria standard. `estrai` dà il testo del corpo (e delle note con `--note`) per `detect.py` e `humanize.py`. `applica` inserisce una lista di modifiche come revisioni tracciate (o già accettate con `--accettate`), conservando corsivi e richiami di nota, e poi verifica da solo: XML valido, rifiutando tutto si torna all'originale, richiami di nota rimasti sulla loro frase (numerati come in Word, anche quando due richiami sono attaccati), numeri, nomi e virgolettati persi o comparsi. Esce con 1 se una modifica non si applica.
- Verificato su un documento di circa 9.000 parole con note a piè di pagina: 12 modifiche applicate con lo script danno lo stesso testo della revisione fatta a mano, e il richiamo di nota da ricontrollare viene segnalato.
- `SKILL.md`: procedura «File Word» con un piccolo council: due revisori indipendenti (Claude e Codex, o due Claude), sintesi che tiene le modifiche concordi e scarta quelle che toccano fatti o posizioni dell'autore, applicazione con `docx.py`, terzo sguardo sulla versione pulita.
- 10 test nuovi (106 in tutto). Lessico, punteggio e benchmark invariati.

## 1.2.0 · 23 novembre 2026

Dalla riunione di brainstorming Claude + Codex del 23/11 e dalla ricerca sui detector di testo IA. Ogni idea aveva un test e un criterio di stop decisi prima dei risultati: qui ci sono gli esiti, anche quelli negativi.

- **Modalità accademica** (`--genere accademico` in `detect.py` e `humanize.py`): citazioni autore-anno, rimandi di pagina e richiami di nota non contano in CONCRETEZZA (il numero di parole resta lo stesso); gli elenchi di nomi, opere e date non contano come triadi. Test registrato sul capitolo di tesi: tell di VOCE da 62 a 44; CONCRETEZZA resta 100 perché la prosa ha comunque 12,3 elementi concreti ogni 100 parole.
- **Misura sul genere accademico** (30 estratti umani di tesi e articoli precedenti al 2022, licenze CC, fuori dal repo, contro 30 gemelli di Claude sugli stessi temi): il punteggio non distingue (AUC 0,52 in modalità accademica; passa il 57% degli umani e il 53% di Claude). SLOP e RITMO vanno al contrario (AUC 0,13 e 0,37), CONCRETEZZA 0,63, VOCE 0,62. Nessuna soglia di genere: `detect.py` lo dice in modalità accademica. `taratura.py` scrive consegne di genere («un brano di una tesi di laurea») e misura la cartella `accademico` in modalità accademica.
- **Mappa** (`detect.py --mappa`): frasi con gerundio dopo la virgola, nominalizzazioni, connettivo in apertura, «È importante che», con una domanda per chi scrive. Test registrato fallito: solo le nominalizzazioni separano (AUC 0,70 su post, 0,62 su tesi); nelle tesi gerundi e connettivi in apertura sono più frequenti negli umani. Non validata, non entra nel punteggio.
- **Domande per l'autore**: ogni tell e ogni categoria del lessico in `slop.json` ha una domanda, e il report di `humanize.py` la mostra. Nel flusso, se chi firma il testo vuole rivederlo, riceve report e mappa e riscrive lui; PASSA è il criterio per fermarsi, non lo scopo.
- **Brief prima di scrivere** (`prima-di-scrivere.md`): in prova. Test registrato in attesa (Solvely e lettura alla cieca su 10 coppie). Dato solo informativo, perché il brief nasce dal lessico di umanizza: `detect.py` in mediana da 86,0 a 93,3, segnalazioni ogni 100 parole da 1,38 a 0,94.
- **Fedeltà**: `detect.py prima.txt dopo.txt` elenca numeri, nomi e virgolettati spariti o comparsi e la quota di parole cambiate (avviso oltre il 30%, stop oltre il 50%, soglie riprese da im-not-ai).
- Regole della riscrittura: un segnale debole da solo non si tocca; quando non intervenire (citazioni, testi anteriori al 2022, lettere, chat). Idee riprese da blader/humanizer (MIT), scritte da capo.
- Modalità generica invariata: sui 507 testi del benchmark nessun punteggio cambia rispetto alla 1.1.1. 26 test nuovi (96 in tutto).

## 1.1.1 · 23 novembre 2026

- `lessico.invisibili`: lo spazio indivisibile (anche stretto) dopo «p.» e «pp.» resta. In una tesi «p. 8» è tipografia voluta: prima `humanize.py` lo toglieva e `detect.py` lo contava fra gli spazi speciali (in un capitolo reale 28 casi, IMPRONTA da 100 a 90). Sui 62 testi del benchmark nessun punteggio cambia. 3 test nuovi (70 in tutto).

## 1.1.0 · 14 ottobre 2026

- Nome: umanizza (prima Sbavatura, poi humanize-it). Dichiarata come humanizer per testi in italiano generati da Claude, perché è tarata e misurata solo su Claude.
- **Taratura personale** (`taratura.py`): importa gli export di Threads, Instagram, Facebook (Meta JSON), LinkedIn (Shares.csv), X (tweets.js) e cartelle di .txt; scrive i gemelli con Claude (API o in chat); misura AUC e coppie vinte per piattaforma; salva soglie personali che possono solo scendere rispetto a 85/70.
- `detect.py`: legge `~/.claude/umanizza/taratura.json` se c'è; opzioni `--taratura`, `--piattaforma`, `--generico`.
- 9 test nuovi con export sintetici nei formati reali (67 in tutto).
- Lessico, pesi e soglie generiche invariati: i numeri del benchmark non cambiano.

## 1.0.0 · 14 ottobre 2026

### Prima di guardare i dati
- Lessico iniziale di 215 voci, 16 tell, scritti a mano.
- Corpus diviso prima di aprirlo: testi generati dispari = dev, pari = test; campioni umani alterni dev/test.

### Taratura sul dev (solo metà dev)
- **Tolti 2 tell** che scattavano più sugli umani che sui modelli: punti esclamativi a raffica, parole in maiuscolo.
- **Aggiunti 5 tell** misurati sul dev: *Non X, ma Y*, *Non serve X: serve Y*, *Sembra X, ma*, *Più X, più Y*, paragrafi *Primo/Secondo/Terzo*.
- Triadi: da soglia fissa a densità (la prima è gratis, ogni altra pesa 0,35).
- Muro di hashtag: contato per riga, non sul testo intero.
- Chiusa che chiede commenti: guarda le ultime due righe, non solo l'ultima.
- **Aggiunte 25 voci** (fatemi sapere, opinione impopolare, ed è proprio questo, la magia sta, sembra un dettaglio, vale la pena, nelle prossime sezioni, questo significa, è un po' come, per chi…).
- IMPRONTA: virgolette curve e "…" non pesano più (gli umani li usano più dei modelli).
- Pesi: ritmo 0,10, concretezza 0,25, slop 0,25, impronta 0,10, voce 0,30.
- Soglie: PASSA ≥ 85, SEGNALATO < 70.
- Audit a mano delle modifiche automatiche sui 222 testi umani del dev: aggettivi e frasi che cambiano senso resi solo segnalati.

### Primo giro sul test
- AUC 0.97 (tweet) / 0.89 (prosa). Testi generati SEGNALATI: 3% (dev: 27%). Risultati in `bench/risultati/*_giro1.json`.

### Revisione indipendente: solo correzioni di bug
- Cancellazioni solo a inizio frase (con virgola o "che") o tra due virgole; mai in grassetto, mai se svuotano la riga.
- Diventate solo segnalate: è chiaro che, è innegabile che, non c'è dubbio che, realizzare che, si pone come, un vero e proprio, a 360 gradi, a tutto tondo, fa la differenza, in virtù di, approcciare, dal momento che, salva tempo, tuttavia, pertanto, in relazione a, viviamo in un'epoca in cui.
- Virgola obbligatoria per in conclusione, in sintesi, in definitiva, per concludere, riassumendo.
- Confini di parola corretti (robustezza non è più "robusta"; un'esperienza, l'ecosistema ora vengono trovati).
- Protetti codice indentato e hashtag. Testo in maiuscolo non toccato. Marchi come iPhone ed eBay non diventano maiuscoli.
- Rifinitura della punteggiatura solo sulle righe cambiate; tolte le regole che toccavano `.env`, `main()`, `:)`, "la la la", "s.p.a.,".
- Lineetta: resta in tutta la riga di dialogo e nei collegamenti senza spazi (Roma–Milano).
- Regex delle triadi in tempo lineare (prima: 120 s su un elenco patologico di 20.000 parole).
- CONCRETEZZA: tolte dal conteggio parole ambigue (prima, secondo, persone, clienti, utenti, ore, anni); corretta la precedenza nel conteggio delle sigle; le frasi urlate non contano.
- Verdetto N/D sotto le 15 parole o su testo non italiano; errori di lettura con codice 2.
- 18 test di regressione, uno per bug.

### Secondo giro sul test
- Pesi e soglie invariati. AUC 0.99 / 0.91. Testi generati SEGNALATI 30%. Umani prosa PASSA 80% (era 87%).
