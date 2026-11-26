"""Lettura 6: prepara le venti coppie alla cieca di un braccio (A o P). Stesso ordine e stesse posizioni nei due bracci."""
import json, random, sys
from pathlib import Path
braccio = sys.argv[1]; assert braccio in ("A", "P")
R = Path.home() / "umanizza-corpus/lettura-cieca-6"; L = R / braccio
def righe(p): return {r.split("|")[0]: r.split("|")[1] for r in p.read_text(encoding="utf-8").splitlines() if r.strip()}
vecchie = righe(Path.home() / "Downloads/umanizza/bench/corpus_ia/consegne.txt")
num = ["04", "05", "09", "11", "14", "18", "20", "23", "25", "26"]
genere = {f"o{i+1:02d}": vecchie[n] for i, n in enumerate(num)} | {f"f{i+1:02d}": vecchie[n] for i, n in enumerate(num)}
rnd = random.Random(20261126)
nomi = sorted(genere); rnd.shuffle(nomi)
posizioni = [True] * 10 + [False] * 10; rnd.shuffle(posizioni)
chiave, blocchi = [], []
for k, nome in enumerate(nomi, 1):
    o = (L / "orig" / f"{nome}.txt").read_text(encoding="utf-8").strip()
    r = (L / "riscritti" / f"{nome}.txt").read_text(encoding="utf-8").strip()
    A, B = (o, r) if posizioni[k - 1] else (r, o)
    chiave.append({"coppia": k, "testo": nome, "A": "originale" if posizioni[k - 1] else "riscritto"})
    blocchi.append(f"## Coppia {k} · {genere[nome]}\n\n### Testo A\n\n{A}\n\n### Testo B\n\n{B}\n")
(L / "giudici" / "coppie.md").write_text("# Venti coppie di testi\n\n" + "\n---\n\n".join(blocchi), encoding="utf-8")
(L / "chiave.json").write_text(json.dumps(chiave, ensure_ascii=False, indent=1), encoding="utf-8")
print(braccio, "coppie:", len(chiave), "| A = originale in", sum(c["A"] == "originale" for c in chiave))
