# Pre-registrazione · lettura 5: riscrive solo Claude

Scritta il 26/11/2026 prima di generare i testi nuovi e prima di qualunque riscrittura.
Decisione del proprietario (26/11/2026, parole sue: «riscrive solo Claude»): in Codex la skill misura e pulisce ma non
riscrive; la riscrittura la fa Claude. Questa prova misura quanto vale quella strada e con quali regole.

## Cosa si sa già (dati di sviluppo: letture 1-4 e braccio 4b)
- Riscritture di Claude su testi di Claude, 20 risposte: 16 (lettura 1, regole 1.6.0), 19 (lettura 3, regole «legami,
  genere, non appiattire»), 13,5 (lettura 4, stesse regole più modifiche puntuali).
- Riscritture di Claude su testi GPT (4b, regole della lettura 4): 11 su 20.
- Riscritture di Codex: 9, 4 e 13 su 20.

## Due bracci, stessi 20 testi, riscrittore sempre Claude
- Braccio A: SKILL.md 1.6.0 pubblicato (commit 39a6042, quello presente al momento della copia), senza modifiche.
- Braccio B: lo stesso SKILL.md con la sola sezione «Regole della riscrittura» sostituita da quella della lettura 3
  (presa da lettura-cieca-4/skill-sperimentale/SKILL.md); il passo 4 resta quello della 1.6.0, senza modifiche.py.
  Il file usato è salvato qui come SKILL-B.md prima delle riscritture.
- Script (detect.py, humanize.py, lessico.py, slop.json) identici nei due bracci: quelli del commit 39a6042, quello presente al momento della copia.

## Materiale (mai riscritto prima)
- 10 testi di Claude, metà di sviluppo del benchmark: haiku_11-19 dispari → c01-c05, sonnet_21-29 dispari → c06-c10.
- 10 testi GPT nuovi, su dieci consegne nuove (consegne_nuove.txt, scritte prima di generare): 31-35 con gpt-6.2-sol →
  g01-g05, 36-40 con gpt-6-luna → g06-g10. Stesso prompt e stesso comando di ~/umanizza-corpus/gpt/genera.sh. Un testo
  per consegna, nessuna rigenerazione, nessuna scelta: se una generazione fallisce si ripete solo quella.
- Riscrittori: quattro agenti Claude nuovi (braccio A e B, gruppo c e g), ognuno con il testo di
  lettura-cieca-4/istruzioni_riscrittore_claude.md, cambiando solo percorsi e nomi dei file. Nessuno vede l'altro braccio.
- Giudici: per ogni braccio un giudice Claude nuovo e un giudice GPT (gpt-6.2-sol via codex exec), con domanda_giudice.txt
  e istruzioni_giudice_claude.md della lettura 4. Venti coppie per braccio, originale in A in 10, seme 20261126.

## Criteri («si legge meglio», pari = mezzo, tutte le 40 risposte del braccio)
1. Scelta del braccio: entra B solo se supera A di almeno 3 risposte su 40 e non ha fatti persi o aggiunti che A non
   ha; altrimenti resta A, cioè le regole di oggi.
2. La strada si applica se il braccio scelto arriva ad almeno 25 su 40 (il valore di oggi). Sotto 25 non cambia nulla:
   SKILL.md, formula e indice restano quelli della 1.6.0.
3. Fedeltà: lessico.confronta_fatti su ogni coppia; ogni numero, nome o virgolettato perso o aggiunto va elencato.
4. Riportati a parte: testi di Claude e testi GPT, giudice Claude e giudice GPT, «sembra di una persona», quota di parole
   cambiate.

## Indice di affidabilità, formula versione 2 (fissata ora)
Se la strada si applica: L usa le 40 risposte del braccio scelto di questa prova; F usa le sue 20 riscritture. Tutto il
resto della formula e i pesi restano uguali. Nel README va scritto che L misura la riscrittura fatta da Claude, perché in
Codex la skill non riscrive più.

## Limiti dichiarati prima
- Scegliere il migliore di due bracci e applicare solo se non peggiora spinge il numero verso l'alto: il margine di 3
  risposte lo attenua, non lo elimina. Va detto nel README accanto all'indice.
- 20 testi e due giudici modello: 2-3 risposte di differenza sono rumore.
- Il giudice Claude giudica riscritture di Claude; il giudice GPT legge 10 originali scritti da GPT.
- I testi GPT nuovi nascono con umanizza già installata in Codex; il comando usa --ignore-user-config e una cartella
  vuota, e il prompt non nomina lo slop.


## Esito (26/11/2026) · NON SI APPLICA
- «Si legge meglio», 40 risposte: braccio A 18 su 40, braccio B 21,5 su 40. B supera A di 3,5 e non ha fatti persi:
  per il criterio 1 il braccio scelto è B. B è sotto 25 su 40: per il criterio 2 la strada non si applica.
  SKILL.md, formula e indice restano quelli della 1.6.0 (7,88).
- Testi di Claude: A 13 su 20, B 13 su 20. Testi GPT: A 5 su 20, B 8,5 su 20.
- Giudice Claude: A 9, B 13 su 20. Giudice GPT: A 9, B 8,5 su 20.
- «Sembra di una persona»: A 33 su 40, B 31 su 40 (testi di Claude 19,5 e 18 su 20; testi GPT 13,5 e 13 su 20).
- Fedeltà: 20 su 20 in tutti e due i bracci.
- Parole cambiate: mediana 11% in A e 7% in B; massimo 34% e 27%. Coppie con le stesse parole dell'originale (cambia
  solo la tipografia o nulla): 4 in A, 7 in B; valgono mezzo punto quando il giudice dice «pari».
- Analisi non pre-registrata, solo descrittiva: sulle riscritture con più del 5% di parole cambiate A fa 13 su 28 e B
  13 su 22; sotto il 5%, A 5 su 12 e B 8,5 su 18.
- Nota: SKILL-B.md differisce dal SKILL.md della lettura 3 solo nella riga description del frontmatter (verificato con diff), che non riguarda la riscrittura.
- Lettura: sui testi di Claude la riscrittura di Claude è preferita in 13 risposte su 20 con tutte e due le regole, sotto
  le 16 e 19 delle letture 1 e 3; sui testi GPT l'originale è preferito in tutti e due i bracci. I giudici trovano le
  riscritture più «da persona» ma non più leggibili. Con 20 testi e due giudici modello 2-3 risposte sono rumore, ma
  nessuno dei due bracci è vicino a 25.
