"""Detector · confronto descrittivo, fatto dopo la conferma: detect.py sugli stessi testi del classificatore.

Non pre-registrato: serve a confrontare le soglie di umanizza (SEGNALATO, DUBBIO) con quelle del classificatore sugli
stessi testi, non a giudicare il classificatore.
"""
import json, sys
from pathlib import Path
CASA = Path.home(); D = CASA / "umanizza-corpus/detector"; C = CASA / "umanizza-corpus"; B = CASA / "Downloads/umanizza/bench"
sys.path.insert(0, str(CASA / "Downloads/umanizza/skills/umanizza"))
import detect, lessico as L
dati = L.carica()
def verdetti(fs):
    v = [detect.analizza(f.read_text(encoding="utf-8"), dati).verdetto for f in fs]
    return {"n": len(v), **{k: v.count(k) for k in sorted(set(v))}}
gruppi = {
    "conferma_umani_web3": sorted((D / "web3").rglob("*.txt")),
    "conferma_umani_partut": sorted((D / "partut").glob("*.txt")),
    "conferma_generati": sorted((D / "gemelli_conferma").glob("*.txt")) + sorted((C / "lettura-cieca-5/gpt_nuovi").glob("*.txt")),
    "verifica_umani": sorted((B / "corpus_umano/test").rglob("*.txt")) + sorted((D / "web2").rglob("*.txt")),
    "verifica_generati": sorted((B / "corpus_ia/test").glob("*.txt")) + sorted((B / "corpus_gpt").glob("*.txt")) + sorted((B / "corpus_claude_forti").rglob("*.txt")),
}
r = {k: verdetti(v) for k, v in gruppi.items()}
(D / "risultati/confronto_detect.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(r, ensure_ascii=False, indent=1))
