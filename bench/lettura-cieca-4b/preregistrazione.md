# Pre-registrazione · braccio 4b: Claude riscrive testi GPT

Scritta il 26/11/2026 prima di qualunque riscrittura e prima di conoscere l'esito della lettura 4.
Condotta da una sessione diversa da quella della lettura 4.

## Perché
Nelle letture 1-4 chi riscrive e chi ha scritto il testo coincidono sempre: c = testi di Claude riscritti da Claude,
g = testi GPT riscritti da Codex. Nessuna prova dice come Claude riscrive un testo GPT. È il caso d'uso che serve se la
riscrittura passa a Claude anche per chi parte da un testo GPT.

## Materiale (mai riscritto prima)
- 10 testi GPT da bench/corpus_gpt: sol_21-25 → x01-x05, luna_26-30 → x06-x10 (copiati in orig/ prima di questa nota).
  Scartati luna_01-05: stesse consegne di sol_01-05, usati nella lettura 1.
- Riscrittore: un agente Claude nuovo, con il testo di lettura-cieca-4/istruzioni_riscrittore_claude.md, cambiando solo
  i nomi dei file (x01…x10) e il percorso della skill.
- Skill: lettura-cieca-4/skill-sperimentale/ (SKILL.md e modifiche.py della lettura 4), letta e non modificata, qualunque
  sia l'esito della lettura 4; gli altri script dalla copia installata. Se nel frattempo la copia installata è stata
  ripristinata alla 1.6.0, gli script restanti sono comunque gli stessi.
- Giudici: gli stessi della lettura 4, con le stesse istruzioni (domanda_giudice.txt, istruzioni_giudice_claude.md), tranne
  «dieci coppie» al posto di «venti». Ordine delle coppie casuale, originale in A in 5 coppie su 10, seme 20261126.
- Si parte solo dopo la chiusura della lettura 4.

## Criteri («si legge meglio», pari = mezzo)
- Principale: giudice GPT, riscritto preferito in almeno 7 coppie su 10 (la soglia che la lettura 4 chiede a Claude dal
  giudice GPT) → Claude riscrive bene anche i testi GPT; sotto 5 → no; in mezzo incerto.
- Secondario, solo riportato: giudice Claude (stesso modello del riscrittore).
- Fedeltà: nessun numero, nome o virgolettato perso o aggiunto (lessico.confronta_fatti); ogni caso va elencato.
- Riportata anche la quota di parole cambiate per testo.

## Limiti dichiarati prima
- Il giudice GPT legge originali scritti da GPT: può preferire il proprio stile. Va contro la riscrittura, non a favore.
- 10 testi e due giudici modello: un esito tra 5 e 7 non decide nulla.
- Un solo riscrittore e una sola esecuzione: non misura la variabilità fra esecuzioni.

## Uso dell'esito
Non entra nell'indice di affidabilità e non cambia SKILL.md: è un'informazione per il proprietario, che decide.

## Esito (26/11/2026) · INCERTO
- Giudice GPT (principale), «si legge meglio»: riscritto 5 su 10 (soglia 7; sotto 5 sarebbe stato no). «Sembra di una
  persona»: 7,5 su 10.
- Giudice Claude (riportato): 6 su 10; «sembra di una persona» 8 su 10.
- Due coppie su dieci sono di fatto identiche e valgono mezzo punto ciascuna: x08 (il report non segnalava nulla) e x01
  (cambiati solo gli apostrofi). Sulle otto coppie con una riscrittura vera: giudice GPT 4 su 8, giudice Claude 5 su 8.
- Per testo (GPT / Claude): x04 1/1, x02 1/1, x09 1/1, x05 1/0, x06 0/1, x10 0/1, x07 0/0, x03 0/0.
- Fedeltà: 10 su 10. Il «perso» segnalato in x02 («un’ultima modifica») è un falso allarme di confronta_fatti: il
  virgolettato c'è, è cambiato solo l'apostrofo da curvo a dritto.
- Parole cambiate: da 0% a 7%, tranne x07 (20%), che perde per tutti e due i giudici.
- x03 perde per tutti e due i giudici per una modifica di humanize.py, non del riscrittore: la lineetta dopo luogo e data
  in apertura di un comunicato («[Città], [data] — …») diventa una virgola.
- Con 10 coppie e due giudici modello, 2-3 coppie di differenza sono rumore: l'esito non dice che Claude riscrive male i
  testi GPT, dice che questa prova non mostra che li riscriva bene.
- Non entra nell'indice e non cambia SKILL.md.
