# Pre-registrazione · lettura 6: riscrittura guidata da un profilo di genere

Scritta il 26/11/2026 prima di qualunque riscrittura.
Richiesta del proprietario: usare dati aperti per tarare la riscrittura («ok entrambi»: profili di genere dai dati aperti
e profilo personale dai suoi testi). Qui si prova solo il profilo di genere; quello personale aspetta i suoi testi.

## Cosa si prova
Lo script nuovo voce.py (taratore, in ~/umanizza-corpus/taratore) misura in che cosa un testo si allontana da un profilo.
I profili di genere sono fatti sul primo campione web (mC4 italiano 2013-2020, 243 testi umani, dati di sviluppo: mai
usati nell'indice): blog 50, articoli 50, azienda 43, comunicati 50, servizi 50. Solo misure aggregate, senza testi.
Escluse dal confronto frasi per capoverso (il corpus ha perso gli a capo) ed emoji (i testi sono precedenti al loro uso).
Per i post dei social e le email non c'è un corpus aperto adatto (i tweet del benchmark hanno frasi di 9 parole): quei
generi restano fuori dalla prova e dal profilo.

## Due bracci, stessi 20 testi, riscrittore sempre Claude
- Braccio A: SKILL.md 1.6.0 (commit 39a6042), senza modifiche.
- Braccio P: lo stesso, più voce.py, i profili e un capoverso «Profilo di genere» dentro il punto 5 (file salvato qui
  come SKILL-P.md): dopo la riscrittura si lancia il confronto con il profilo del genere, si correggono gli scarti dove si
  può senza cambiare fatti né spezzare i periodi, un solo giro.
- Al riscrittore del braccio P si dice il genere di ogni testo; a quello del braccio A no (non gli serve).

## Materiale (mai riscritto prima)
Testi di Claude Opus e Claude Fable del benchmark (bench/corpus_claude_forti), per le dieci consegne di genere coperto:
04 e 05, 11, 14, 18, 26 → blog; 09 e 25 → servizi; 20 → azienda; 23 → comunicati. opus → o01-o10, fable → f01-f10,
nell'ordine 04 05 09 11 14 18 20 23 25 26. Quattro agenti Claude nuovi (braccio × modello), istruzioni della lettura 4.
Giudici: per braccio un giudice Claude nuovo e un giudice GPT (gpt-6.2-sol), domanda e istruzioni delle letture 4 e 5.
Venti coppie per braccio, originale in A in 10, seme 20261126.

## Criteri («si legge meglio», pari = mezzo, 40 risposte per braccio)
1. Il profilo di genere si propone per SKILL.md solo se P supera A di almeno 3 risposte su 40 e non ha fatti persi o
   aggiunti che A non ha. Altrimenti non si propone.
2. Fedeltà: lessico.confronta_fatti su ogni coppia, ogni caso elencato.
3. Riportati: testi Opus e Fable, giudice Claude e GPT, «sembra di una persona», parole cambiate, vicinanza al profilo
   prima e dopo nei due bracci.

## Indice di affidabilità
Non cambia in nessun caso con questa prova: qui i testi sono solo di Claude e riscrive solo Claude, una composizione
diversa da quella della formula (lettura 1). Per cambiare L servirebbe una prova con la composizione della formula.

## Limiti dichiarati prima
- I profili vengono da pagine web del 2013-2020, più lunghe e di altro tempo rispetto ai testi generati.
- La vicinanza al profilo non separa umano e IA (AUC 0,61 su prosa): è una guida di stile, non un rilevatore, e la prova
  non riguarda i detector.
- Testi lunghi (mediana oltre 350 parole): i giudici leggono molto, e le coppie poco cambiate valgono mezzo punto.
- 20 testi, due giudici modello: 2-3 risposte sono rumore.


## Esito (26/11/2026) · IL PROFILO DI GENERE NON SI PROPONE
- «Si legge meglio», 40 risposte: braccio A 28,5 su 40, braccio P 19 su 40. P è sotto A di 9,5 risposte: per il
  criterio 1 il profilo di genere non si propone per SKILL.md.
- Testi di Opus: A 15,5 e P 7 su 20. Testi di Fable: A 13 e P 12 su 20.
- Giudice Claude: A 13,5 e P 10 su 20. Giudice GPT: A 15 e P 9 su 20.
- «Sembra di una persona»: A 39,5 e P 35,5 su 40.
- Vicinanza al profilo, mediana: da 80,6 a 80,8 in A; da 80,6 a 84,4 in P. Il profilo ha fatto quello che doveva
  (avvicinare le misure) e la lettura è peggiorata.
- Fedeltà: nessun fatto perso. Le voci segnalate sono solo maiuscole cambiate: il titolo di o09 passato da Title Case
  a maiuscola iniziale (tutti e due i bracci) e «Ufficio Stampa» diventato «Ufficio stampa» in o08 (braccio P).
- Parole cambiate: mediana 12% in A e 10% in P.
- Dai rapporti dei riscrittori del braccio P: per seguire il profilo le domande dirette sono diventate indirette, il «tu»
  al cliente è diventato «il cliente», i due punti sono stati tolti. I giudici citano proprio queste modifiche tra i
  motivi per preferire l'originale.
- Nota a margine, non pre-registrata: il braccio A, cioè la skill di oggi, su articoli, pagine e comunicati lunghi di Opus
  e Fable fa 28,5 su 40, più che sui post brevi delle letture 1-5. Non entra nell'indice: composizione diversa.
- Limiti: 20 testi, due giudici modello; il giudice Claude non è stato trascritto con i motivi (sono nei rapporti).
