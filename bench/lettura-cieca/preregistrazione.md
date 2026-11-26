# Pre-registrazione · la riscrittura di umanizza si legge meglio?

Scritta il 26/11/2026 prima di qualunque riscrittura.

## Materiale
- 10 testi di Claude dalla metà di test (haiku_02-10, sonnet_12-20: 10 consegne diverse) → c01-c10.
- 10 testi di GPT (sol_01-05, luna_06-10: 10 consegne diverse) → g01-g10.
- Riscrittura con umanizza: Claude (subagente nuovo, segue SKILL.md) riscrive i testi c; Codex con la skill
  installata riscrive i testi g. Nessun dato nuovo e nessun segnaposto {{…}}: non c'è un autore che li riempia.

## Giudizio alla cieca
- Coppie originale/riscritto in ordine A/B casuale (seme fisso), chiave in un file a parte che i giudici non vedono.
- Due giudici che non sanno cosa è umanizza: un subagente Claude nuovo e Codex (GPT). Ognuno giudica tutte le 20 coppie.
- Domande per coppia: quale si legge meglio (A, B, pari); quale sembra scritto da una persona (A, B, pari).
- Principale: giudizio incrociato (GPT giudica le riscritture di Claude, Claude quelle di GPT), 20 giudizi.
- Secondario: stesso modello, e tutte le 40 risposte.
- Fedeltà: `detect.py originale riscritto` per ogni coppia; conta numeri, nomi e virgolettati comparsi.

## Criteri (giudizio incrociato, «si legge meglio»; i pari contano mezzo)
- Migliora: riscritto preferito in almeno 14 coppie su 20 (70%) e nessun fatto inventato.
- Non migliora: meno di 11 su 20 (55%).
- Tra 11 e 14: incerto.
- Un fatto inventato (numero o nome comparso che non è nell'originale) va riportato, qualunque sia l'esito.

## Limite dichiarato
I giudici sono modelli, non persone. Il giudizio incrociato riduce la preferenza di un modello per il proprio stile, non la elimina.

## Modifica prima del giudizio (26/11/2026)
Il sorteggio libero metteva l'originale in A in 14 coppie su 20: con un giudice sensibile alla posizione avrebbe
pesato sul risultato. Prima di qualunque giudizio: ordine bilanciato, originale in A in 10 coppie e in B in 10,
sempre con seme fisso. Nessun'altra modifica.

## Esito (26/11/2026) · INCERTO sulla leggibilità, chiaro sull'aspetto umano
- Giudizio incrociato, «si legge meglio»: riscritto preferito in 12 coppie su 20 → incerto (tra 11 e 14).
- Giudizio incrociato, «sembra di una persona»: riscritto preferito in 16,5 su 20.
- Tutte le 40 risposte: meglio 25/40, persona 34,5/40. Posizione: i giudici scelgono A in 12/20 e 11/20 (originale in A in 10/20).
- Per chi riscrive: le riscritture di Claude sono preferite da entrambi i giudici in 8 coppie su 10;
  quelle di Codex (GPT) in 4/10 (giudice Claude) e 5/10 (giudice GPT).
- Fedeltà: nessun numero, nome o virgolettato perso o aggiunto in 20 riscritture su 20. In c09 una frase tecnica
  è stata corretta (LoRA/QLoRA): cambiamento di contenuto, non un dato nuovo.
- Limite: giudici modelli, non persone.
