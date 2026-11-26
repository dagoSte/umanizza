#!/usr/bin/env python3
"""umanizza · prepara_web.py — testi web italiani anteriori al 2021, divisi per genere, per il confronto a parità di genere.

Fonte: mC4 italiano (Hugging Face allenai/c4, Common Crawl fino al 2020), file di validazione da circa 29 MB (otto in tutto).
I testi non sono inclusi nel repo: questo script li scarica e rifà la selezione, sempre uguale.

    python3 bench/prepara_web.py bench/corpus_web                 # scarica e seleziona
    python3 bench/prepara_web.py bench/corpus_web --file c4.json.gz   # usa un file già scaricato
    python3 bench/prepara_web.py bench/corpus_web2 --shard 1          # secondo campione (verifica della 1.6.0)

Selezione (fissata prima di leggere i testi, vedi CHANGELOG 1.5.0): anno ≤ 2020; 100-400 parole; niente «cookie»,
«©», «lorem ipsum»; almeno 4 fine frase; righe sotto le 6 parole al massimo il 30%; genere dal percorso dell'URL;
al massimo 50 testi per genere, i primi del file che passano.
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
import urllib.request
from pathlib import Path

URL = "https://huggingface.co/datasets/allenai/c4/resolve/main/multilingual/c4-it-validation.tfrecord-{n:05d}-of-00008.json.gz"
MAX_PER_GENERE = 50
GENERI = [  # primo che corrisponde, in quest'ordine
    ("blog", ("/blog",)),
    ("articoli", ("/news", "notizi", "articol")),
    ("azienda", ("chi-siamo", "chisiamo", "about", "azienda")),
    ("comunicati", ("comunicat", "press")),
    ("servizi", ("serviz", "prodott")),
]


def genere(url: str) -> str | None:
    percorso = re.sub(r"^[a-z]+://[^/]+", "", url.lower())
    for nome, chiavi in GENERI:
        if any(k in percorso for k in chiavi):
            return nome
    return None


def passa(testo: str, timestamp: str) -> bool:
    if not timestamp[:4].isdigit() or int(timestamp[:4]) > 2020:
        return False
    parole = len(testo.split())
    if not 100 <= parole <= 400:
        return False
    basso = testo.lower()
    if "cookie" in basso or "©" in testo or "lorem ipsum" in basso:
        return False
    if len(re.findall(r"[.!?](\s|$)", testo)) < 4:
        return False
    righe = [r for r in testo.splitlines() if r.strip()]
    corte = sum(1 for r in righe if len(r.split()) < 6)
    return corte <= 0.3 * len(righe)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("cartella")
    ap.add_argument("--file", help="file .json.gz già scaricato (altrimenti lo scarica da Hugging Face)")
    ap.add_argument("--shard", type=int, default=0, help="quale degli 8 file di validazione (0-7); 0 = primo campione, 1 = secondo")
    a = ap.parse_args(argv)
    out = Path(a.cartella)
    sorgente = Path(a.file) if a.file else out / f"c4-it-validation-{a.shard:05d}.json.gz"
    if not sorgente.exists():
        out.mkdir(parents=True, exist_ok=True)
        url = URL.format(n=a.shard)
        print(f"Scarico {url} (circa 29 MB)…")
        urllib.request.urlretrieve(url, sorgente)
    conta = {nome: 0 for nome, _ in GENERI}
    fonti = []
    with gzip.open(sorgente, "rt", encoding="utf-8") as f:
        for riga in f:
            d = json.loads(riga)
            g = genere(d.get("url", ""))
            if g is None or conta[g] >= MAX_PER_GENERE or not passa(d["text"], d.get("timestamp", "")):
                continue
            conta[g] += 1
            cartella = out / g
            cartella.mkdir(parents=True, exist_ok=True)
            nome = f"{g}_{conta[g]:02d}.txt"
            (cartella / nome).write_text(d["text"].strip() + "\n", encoding="utf-8")
            fonti.append({"file": f"{g}/{nome}", "url": d["url"], "timestamp": d["timestamp"]})
    (out / "fonti.json").write_text(json.dumps(fonti, ensure_ascii=False, indent=1), encoding="utf-8")
    print("Testi per genere: " + ", ".join(f"{k} {v}" for k, v in conta.items()) + f" · totale {sum(conta.values())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
