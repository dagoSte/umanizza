"""Lettura 5: prepara le venti coppie alla cieca di un braccio (A o B). Stesso ordine e stesse posizioni nei due bracci."""
import json, random, sys
from pathlib import Path
braccio = sys.argv[1]; assert braccio in ("A", "B")
R = Path.home() / "umanizza-corpus/lettura-cieca-5"; L = R / braccio
def righe(p): return {r.split("|")[0]: r.split("|")[1] for r in p.read_text(encoding="utf-8").splitlines() if r.strip()}
vecchie = righe(Path.home() / "Downloads/umanizza/bench/corpus_ia/consegne.txt"); nuove = righe(R / "consegne_nuove.txt")
num_c = ["11", "13", "15", "17", "19", "21", "23", "25", "27", "29"]; num_g = [str(n) for n in range(31, 41)]
genere = {f"c{i+1:02d}": vecchie[n] for i, n in enumerate(num_c)} | {f"g{i+1:02d}": nuove[n] for i, n in enumerate(num_g)}
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
