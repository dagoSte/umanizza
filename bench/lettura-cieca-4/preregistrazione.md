# Pre-registrazione · modifiche puntuali con verifica alla cieca (1.7.0)

Scritta il 26/11/2026 prima di scrivere il codice nuovo e prima di qualunque riscrittura.

## Diagnosi
Nelle prove 1-3 Codex legge il report e riscrive il testo intero da capo (`cat > finale.txt`): il risultato è un testo
nuovo nel suo stile, con frasi spezzate e accorciate. Come giudice, GPT preferisce l'originale alle riscritture di Codex.

## Modifica
1. Nuovo script `modifiche.py`. La riscrittura diventa un elenco di modifiche puntuali (`modifiche.json`: testo esatto da
   cambiare in pulito.txt, testo nuovo, motivo), applicate dallo script; il resto del testo non cambia.
2. Verifica alla cieca: `modifiche.py prova` mostra per ogni modifica la frase in due versioni, X e Y, in ordine casuale;
   chi riscrive sceglie; `modifiche.py applica --scelte` tiene solo le modifiche preferite all'originale (pari = originale).
3. In SKILL.md tornano le regole della prova 3 (tenere i legami, rispettare il genere, non appiattire; via «Varia il ritmo»).

## Materiale nuovo (mai riscritto prima)
- 10 testi GPT: sol_16-20, luna_21-25 → g01-g10, riscritti da Codex.
- 10 testi Claude della metà di sviluppo del benchmark (mai usati nelle letture): haiku_01-09 dispari, sonnet_11-19 dispari
  → c01-c10, riscritti da un agente Claude nuovo. (La metà di test è esaurita dalle prove 1-3.)
- Stesse istruzioni ai riscrittori e ai giudici; ordine A/B bilanciato 10/10, seme fisso.

## Criteri (giudizio incrociato, «si legge meglio», pari = mezzo)
- Successo: almeno 14 coppie su 20.
- Condizione del proprietario: se la media incrociata è sotto 12 su 20 (prima prova) o le 40 risposte sotto 25, non si applica.
- Codex: riscritture GPT preferite dal giudice Claude in almeno 6,5 su 10. Claude: preferite dal giudice GPT in almeno 7 su 10.
- Fedeltà: nessun numero, nome o virgolettato perso o aggiunto.
- Indice: se si applica, L usa le 40 risposte di questa prova.

## Esito (26/11/2026) · NON SI APPLICA
- Giudizio incrociato, «si legge meglio»: 11 su 20 → incerto (criterio di successo 14); sotto i 12 della prima prova:
  per la condizione del proprietario non si applica.
- Tutte le 40 risposte: 26,5 su 40 (prima prova 25). «Sembra di una persona», incrociato: 15,5 su 20.
- Codex: preferito 5/10 dal giudice Claude (soglia 6,5; prove precedenti 4, 3, 0) e 8/10 dal giudice GPT.
- Claude: preferito 6/10 dal giudice GPT (soglia 7; prima prova 8) e 7,5/10 dal giudice Claude. Parole cambiate in mediana 6%.
- Fedeltà: 20 riscritture su 20 senza fatti persi o aggiunti. Entrambi i riscrittori hanno seguito il flusso (modifiche.json,
  confronto alla cieca, applica); Claude ha scartato 4 modifiche nel confronto.
- Lettura: il flusso migliora Codex e frena Claude. Con 10 coppie per gruppo e due giudici modello, differenze di 2-3 coppie
  sono nel rumore: per decidere serve un campione più grande o lettori umani.
- Ripristino: SKILL.md e copie installate come nella 1.6.0, modifiche.py tolto (copia in skill-sperimentale/).
