"""Detector · scrive consegne.jsonl: un gemello per ogni testo umano di sviluppo (web1 e UD dev)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "Downloads/umanizza/skills/umanizza"))
import lessico as L
CASA = Path.home()
GENERE = {
    "blog": "un articolo per un blog", "articoli": "un articolo di notizie per un sito web",
    "azienda": "la pagina «chi siamo» del sito di un'azienda", "comunicati": "un comunicato stampa",
    "servizi": "la pagina di un sito che descrive un servizio o un prodotto",
    "prosa": "un brano in prosa, come in un articolo di giornale, una voce enciclopedica o un testo normativo, secondo l'argomento",
    "social": "alcuni tweet, uno per riga",
}
FONTI = [(g, CASA / "umanizza-corpus/web/selezione" / g) for g in ("articoli", "azienda", "blog", "comunicati", "servizi")]
FONTI += [(g, CASA / "Downloads/umanizza/bench/corpus_umano/dev" / g) for g in ("prosa", "social")]
GENERATORI = ["claude-haiku-5-5", "gpt-6.2-sol", "claude-sonnet-5-5", "gpt-6-luna"]
righe, i = [], 0
for genere, cartella in FONTI:
    for f in sorted(cartella.glob("*.txt")):
        testo = f.read_text(encoding="utf-8").strip()
        n = len(L.parole(testo)); inizio = " ".join(testo.split()[:20])
        oggetto = "testo" if genere != "social" else "serie di tweet"
        prompt = (f"Scrivi in italiano {GENERE[genere]} di circa {n} parole. "
                  f"L'argomento è quello di un {oggetto} che inizia così: «{inizio}…». "
                  "Rispondi solo con il testo, senza introduzioni né note.")
        righe.append({"id": f"{genere}__{f.stem}", "genere": genere, "umano": str(f), "parole": n,
                      "generatore": GENERATORI[i % 4], "prompt": prompt}); i += 1
out = Path(__file__).resolve().parents[1] / "consegne.jsonl"
out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in righe), encoding="utf-8")
from collections import Counter
print(len(righe), Counter(r["generatore"] for r in righe), Counter((r["genere"], r["generatore"][:6]) for r in righe).most_common(3))
