# Classificatore addestrato: si replicano i detector seri?

Esperimento del 27 novembre 2026. Un BERT italiano (`dbmdz/bert-base-italian-xxl-cased`, MIT) addestrato su coppie di testi umani e generati sullo stesso tema, con lo stesso principio di Pangram, poi verificato sugli stessi testi dell'indice di affidabilità e su testi nuovi. Non fa parte della skill: è una misura, e non va usato per guidare o scegliere riscritture.

Resoconto e numeri in [docs/validazione.md](../../docs/validazione.md#classificatore-addestrato-si-replicano-i-detector-seri).

## Cosa c'è

| File | Contenuto |
|---|---|
| `preregistrazione.md` | criteri della corsa ufficiale, scritti prima; correzione dei gemelli prima della corsa; esito (REGGE IN PARTE) |
| `conferma.md` | criteri della prova di conferma con soglia 0,99, scritti prima; esito (NON REGGE) e difetto dei dati di ParTUT |
| `script/` | gli script eseguiti, senza modifiche |
| `risultati/` | esiti in JSON, probabilità del classificatore per gruppo, prova parziale (non conta), confronto con `detect.py` |
| `gemelli/`, `consegne_web.jsonl` | i 243 testi generati come gemelli delle pagine web di addestramento, con le consegne |
| `gemelli_conferma/`, `consegne_conferma.jsonl` | i 40 testi generati per la conferma |

## Cosa non c'è

- **I pesi del modello** (445 MB scaricati, 443 MB addestrati): si ricostruiscono con gli script.
- **I testi umani**: le pagine web mC4 si riscaricano con `bench/prepara_web.py` (`--shard 0`, `1`, `2`); la prosa e i tweet UD con `bench/prepara_umano.py`; ParTUT dal suo repository Universal Dependencies.
- **I 222 gemelli dei testi UD**: le consegne citano l'inizio di testi con licenza non commerciale (CC BY-NC-SA).

## Come rifarlo

Servono Python 3.13 con `torch`, `transformers` e `scikit-learn`; su un Mac M1 l'addestramento dura circa 10 minuti. Gli script lavorano in una cartella fuori dal repo, `~/umanizza-corpus/detector`, e cercano il repo in `~/Downloads/umanizza`: i percorsi sono in cima a ogni file.

1. `consegne.py` scrive le consegne; `genera_uno.sh` genera un gemello (Claude con `claude -p`, GPT con `codex exec`); `rigenera.sh` ritenta i rifiuti.
2. `classifica.py` addestra, verifica sui 12 confronti dell'indice e scrive `esito.json`; con `--salva` salva il modello.
3. `conferma.py` verifica il modello salvato sui testi nuovi a soglia 0,99.
4. `confronto_detect.py` misura `detect.py` sugli stessi testi.

I testi generati non si rigenerano identici: chi rifà l'esperimento ottiene gemelli diversi e numeri vicini, non uguali.
