# Pre-registrazione · prova di conferma del classificatore, soglia 0,99

Scritta il 27/11/2026 prima di scaricare i testi nuovi, di generare i testi di conferma e di riaddestrare.
Richiesta del proprietario: «ottimo,» e «si» alla proposta di una prova di conferma con soglia fissata.

## Perché
La corsa ufficiale (preregistrazione.md) ha dato REGGE IN PARTE: riconoscimento sopra detect.py, ma 6,9% di testi umani
accusati a soglia 0,5. A posteriori, con soglia 0,99, gli umani accusati sarebbero stati il 2,8%. Una soglia scelta
guardando i risultati non vale: va provata su testi che nessuno ha ancora visto.

## Modello
Il modello della corsa ufficiale non è stato salvato. Si riaddestra con impostazioni, dati e seme identici e questa volta
si salva. Addestrare su MPS non è riproducibile bit per bit: si riportano di nuovo i 12 confronti e la quota di umani
sopra 0,99 sui 464 testi di verifica, accanto a quelli della corsa ufficiale. Se l'AUC media si scosta di più di 0,01,
lo si dice e la prova va letta con quella cautela. Nessuna altra modifica.

## Testi nuovi (mai visti, né in addestramento né in verifica)
- Umani web: terzo campione mC4 (shard 00002), con bench/prepara_web.py e la stessa selezione (al massimo 50 per genere).
- Umani prosa formale: UD Italian-ParTUT (testi giuridici, Wikipedia e articoli, in parte tradotti; CC BY-NC-SA, non va
  nel repo), file dev e test, tagliati con la funzione e i parametri della prosa del benchmark (80-170 parole). È il
  genere su cui il classificatore sbagliava di più.
- Generati: 40 gemelli di testi del terzo campione web, scelti a caso con seme 20261127, 10 a testa da
  claude-sonnet-5-5, claude-opus-5-5, gpt-6.2-sol, gpt-6-luna, con la consegna corretta della corsa ufficiale. Più i
  10 testi GPT generati per la quinta lettura alla cieca (consegne 31-40), mai usati dal classificatore. Tutti i testi
  passano dalla stessa normalizzazione.

## Criteri (soglia 0,99 sulla probabilità di testo generato)
1. Umani accusati: al massimo il 3% di tutti i testi umani nuovi (web e ParTUT insieme).
2. Generati riconosciuti: almeno l'85% dei 50 testi generati nuovi.
- 1 e 2: REGGE con soglia 0,99. Solo uno dei due: NON REGGE (la soglia sposta il problema invece di risolverlo).
- Riportati: quote per gruppo (web per genere, ParTUT, generati per modello), AUC umani nuovi contro generati nuovi,
  e gli stessi numeri a soglia 0,5.

## Uso
Come prima: misura, mai bersaglio per guidare riscritture. Nel repo solo se il proprietario lo chiede.

## Esito (27/11/2026) · NON REGGE
- Riaddestramento: AUC media sui 12 confronti 0,991 (corsa ufficiale 0,9905; scarto 0,0005, entro 0,01); umani di verifica
  sopra 0,99: 11 su 464 (corsa ufficiale 13). Tokenizzazione del modello salvato identica all'originale.
- Criterio 1: a soglia 0,99, 15 testi umani nuovi su 262 giudicati generati (5,7%; criterio ≤ 3%). NON SODDISFATTO.
  Web: 8 su 231 (articoli 2/50, azienda 1/31, blog 2/50, comunicati 0/50, servizi 3/50). ParTUT: 7 su 31.
- Criterio 2: 48 generati nuovi su 50 riconosciuti (96%; criterio ≥ 85%). SODDISFATTO. Sonnet 9/10, Opus 9/10,
  GPT 10/10, 10/10 e 10/10.
- AUC umani nuovi contro generati nuovi: 0,988. A soglia 0,5: 38 umani su 262 (14,5%) e 50 generati su 50.
- Difetto dei dati scoperto dopo: ParTUT e la prosa del benchmark (ISDT) condividono documenti. Dei 31 brani ParTUT, 11
  hanno almeno una frase in comune con la prosa di sviluppo (usata come umana in addestramento) e 12 con la prosa di
  verifica (su cui era stata scelta a posteriori la soglia 0,99); solo 8 sono davvero nuovi. Senza i 23 brani contaminati,
  descrittivo: 9 umani accusati su 239 (3,8%). Il solo web: 8 su 231 (3,5%). L'esito non cambia: NON REGGE.
- Accusati, a occhio: testi normativi UE e prosa tradotta (ParTUT), pagine commerciali di servizi e aziende (web).
- Lettura: la soglia alta riduce le accuse (sul web da circa il 6% a circa il 3,5%) senza perdere quasi nulla del
  generato, ma non le porta sotto il 3%, e sulla prosa formale e tradotta resta alta. Lo stesso limite dei detector
  commerciali, in scala più grande.
