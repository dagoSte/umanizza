#!/usr/bin/env python3
"""umanizza · modifiche.py — riscrittura a modifiche puntuali, con verifica alla cieca di ogni modifica.

Chi riscrive non produce un testo nuovo: scrive un elenco di modifiche, una per frase segnalata, e lo script le applica.
Il resto del testo resta parola per parola.

    python3 modifiche.py prova pulito.txt modifiche.json            # confronto.md: ogni modifica come X e Y, in ordine casuale
    python3 modifiche.py applica pulito.txt modifiche.json --scelte scelte.json -o riscritto.txt

modifiche.json:  [{"vecchio": "testo esatto in pulito.txt", "nuovo": "testo nuovo", "motivo": "segnalazione"}, ...]
scelte.json:     {"1": "X", "2": "Y", "3": "pari", ...}   (si tiene una modifica solo se la versione scelta è quella nuova;
                                                            pari = resta l'originale)
Senza --scelte, applica tutte le modifiche. Esce con 1 se una modifica non si applica (testo non trovato o non unico).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lessico as L  # noqa: E402

_FINE = re.compile(r"[.!?…](?=\s|$)|\n")


def carica(path: str | Path) -> list[dict]:
    dati = json.loads(Path(path).read_text(encoding="utf-8"))
    mods = dati["modifiche"] if isinstance(dati, dict) else dati
    for m in mods:
        if not isinstance(m.get("vecchio"), str) or not m["vecchio"] or not isinstance(m.get("nuovo"), str):
            raise ValueError(f"modifica non valida: {m!r}")
    return mods


def controlla(testo: str, mods: list[dict]) -> list[str]:
    """Errori che impediscono di applicare: testo non trovato, non unico, modifiche sovrapposte."""
    errori, spazi = [], []
    for i, m in enumerate(mods, 1):
        n = testo.count(m["vecchio"])
        if n != 1:
            errori.append(f"modifica {i}: «{m['vecchio'][:60]}» {'non trovato' if n == 0 else f'trovato {n} volte'}")
            continue
        a = testo.index(m["vecchio"])
        spazi.append((a, a + len(m["vecchio"]), i))
    spazi.sort()
    for (a1, b1, i1), (a2, b2, i2) in zip(spazi, spazi[1:]):
        if a2 < b1:
            errori.append(f"modifiche {i1} e {i2} si sovrappongono")
    return errori


def applica(testo: str, mods: list[dict], tenere: set[int] | None = None) -> str:
    """Applica le modifiche (numerate da 1) da destra a sinistra; con `tenere`, solo quelle indicate."""
    scelte = [(testo.index(m["vecchio"]), i, m) for i, m in enumerate(mods, 1) if tenere is None or i in tenere]
    for a, _, m in sorted(scelte, reverse=True):
        testo = testo[:a] + m["nuovo"] + testo[a + len(m["vecchio"]):]
    return testo


def _frase(testo: str, a: int, b: int) -> tuple[int, int]:
    """Estremi della frase (o delle frasi) che contengono testo[a:b]."""
    inizio = 0
    for f in _FINE.finditer(testo, 0, a):
        inizio = f.end()
    f = _FINE.search(testo, b)
    fine = f.end() if f else len(testo)
    return inizio, fine


def prova(testo: str, mods: list[dict]) -> tuple[str, dict]:
    """Foglio di confronto: per ogni modifica la frase originale e quella nuova, come X e Y in ordine casuale."""
    seme = int(hashlib.sha256((testo + json.dumps(mods, ensure_ascii=False)).encode()).hexdigest()[:8], 16)
    rnd = random.Random(seme)
    righe = ["# Confronto alla cieca", "",
             "Per ogni modifica leggi le due versioni come un lettore di quel tipo di testo e scegli quella che si legge meglio",
             "(più chiara, scorrevole, naturale). Rispondi in scelte.json: {\"1\": \"X\", \"2\": \"Y\", \"3\": \"pari\", ...}.",
             "Non aprire confronto.json prima di aver scelto.", ""]
    mappa = {}
    for i, m in enumerate(mods, 1):
        a = testo.index(m["vecchio"])
        s, e = _frase(testo, a, a + len(m["vecchio"]))
        prima = testo[s:e].strip()
        dopo = (testo[s:a] + m["nuovo"] + testo[a + len(m["vecchio"]):e]).strip()
        x_nuova = rnd.random() < 0.5
        mappa[str(i)] = {"X": "nuovo" if x_nuova else "originale"}
        x, y = (dopo, prima) if x_nuova else (prima, dopo)
        righe += [f"## Modifica {i}", "", f"X: {x}", "", f"Y: {y}", ""]
    return "\n".join(righe), mappa


def da_tenere(scelte: dict, mappa: dict) -> set[int]:
    tenere = set()
    for k, v in scelte.items():
        v = str(v).strip().upper()
        if k in mappa and v in ("X", "Y"):
            scelta = mappa[k]["X"] if v == "X" else ("originale" if mappa[k]["X"] == "nuovo" else "nuovo")
            if scelta == "nuovo":
                tenere.add(int(k))
    return tenere


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prova", help="crea il confronto alla cieca")
    p.add_argument("testo"); p.add_argument("modifiche"); p.add_argument("-o", "--out", default="confronto.md")
    q = sub.add_parser("applica", help="applica le modifiche (solo quelle preferite, con --scelte)")
    q.add_argument("testo"); q.add_argument("modifiche"); q.add_argument("--scelte")
    q.add_argument("--confronto", help="mappa del confronto (predefinito: confronto.json accanto a scelte.json)")
    q.add_argument("-o", "--out", required=True)
    a = ap.parse_args(argv)

    testo = Path(a.testo).read_text(encoding="utf-8")
    mods = carica(a.modifiche)
    errori = controlla(testo, mods)
    if errori:
        print("\n".join(errori), file=sys.stderr)
        return 1
    if a.cmd == "prova":
        foglio, mappa = prova(testo, mods)
        Path(a.out).write_text(foglio + "\n", encoding="utf-8")
        Path(a.out).with_suffix(".json").write_text(json.dumps(mappa, indent=1), encoding="utf-8")
        print(f"{len(mods)} modifiche da confrontare in {a.out}")
        return 0
    tenere = None
    if a.scelte:
        confronto = Path(a.confronto) if a.confronto else Path(a.scelte).with_name("confronto.json")
        mappa = json.loads(confronto.read_text(encoding="utf-8"))
        tenere = da_tenere(json.loads(Path(a.scelte).read_text(encoding="utf-8")), mappa)
    nuovo = applica(testo, mods, tenere)
    Path(a.out).write_text(nuovo, encoding="utf-8")
    tenute = len(mods) if tenere is None else len(tenere)
    f = L.confronta_fatti(testo, nuovo)
    print(f"modifiche tenute: {tenute} su {len(mods)} · parole cambiate {f['cambiato']:.0%}")
    if f["persi"] or f["nuovi"]:
        print(f"  attenzione · spariti: {', '.join(f['persi']) or '-'} · comparsi: {', '.join(f['nuovi']) or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
