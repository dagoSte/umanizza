"""Prepara le dieci coppie alla cieca del braccio 4b: ordine casuale, originale in A in 5 su 10, chiave a parte."""
import json, random
from pathlib import Path
L = Path.home() / "umanizza-corpus/lettura-cieca-4b"
consegne = {r.split("|")[0]: r.split("|")[1] for r in (Path.home() / "Downloads/umanizza/bench/corpus_ia/consegne.txt").read_text(encoding="utf-8").splitlines() if r.strip()}
num = ["21", "22", "23", "24", "25", "26", "27", "28", "29", "30"]
genere = {f"x{i+1:02d}": consegne[n] for i, n in enumerate(num)}
rnd = random.Random(20261126)
nomi = sorted(genere); rnd.shuffle(nomi)
posizioni = [True] * 5 + [False] * 5; rnd.shuffle(posizioni)
chiave, blocchi = [], []
for k, nome in enumerate(nomi, 1):
    o = (L / "orig" / f"{nome}.txt").read_text(encoding="utf-8").strip()
    r = (L / "riscritti" / f"{nome}.txt").read_text(encoding="utf-8").strip()
    A, B = (o, r) if posizioni[k - 1] else (r, o)
    chiave.append({"coppia": k, "testo": nome, "A": "originale" if posizioni[k - 1] else "riscritto"})
    blocchi.append(f"## Coppia {k} · {genere[nome]}\n\n### Testo A\n\n{A}\n\n### Testo B\n\n{B}\n")
(L / "giudici" / "coppie.md").write_text("# Dieci coppie di testi\n\n" + "\n---\n\n".join(blocchi), encoding="utf-8")
(L / "chiave.json").write_text(json.dumps(chiave, ensure_ascii=False, indent=1), encoding="utf-8")
print("coppie:", len(chiave), "| A = originale in", sum(c["A"] == "originale" for c in chiave))
