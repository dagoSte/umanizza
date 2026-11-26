#!/usr/bin/env python3
"""Misura umanizza: quanto separa testi generati da testi scritti da persone.

Uso:
  python3 bench.py --ia CARTELLA_IA --umano CARTELLA_UMANO [--umano ALTRA] [--json]

Stampa per ogni gruppo: mediana del punteggio, quota PASSA/DUBBIO/SEGNALATO,
mediane dei cinque controlli; poi l'AUC (probabilità che un testo umano preso
a caso abbia punteggio più alto di un testo IA preso a caso; 0.50 = moneta)
e il tasso di falsi positivi (testi umani SEGNALATI).

Se passi --umano più volte, ogni cartella è un gruppo a sé.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

QUI = Path(__file__).resolve().parent
sys.path.insert(0, str(QUI.parent / "skills" / "umanizza"))
import detect  # noqa: E402
import lessico as L  # noqa: E402

CONTROLLI = ["ritmo", "concretezza", "slop", "impronta", "voce"]


def auc(pos: list[float], neg: list[float]) -> float:
    """P(pos > neg) con i pari che contano metà (Mann-Whitney)."""
    if not pos or not neg:
        return float("nan")
    vinte = 0.0
    for p in pos:
        for n in neg:
            vinte += 1.0 if p > n else 0.5 if p == n else 0.0
    return vinte / (len(pos) * len(neg))


def gruppo(cartella: Path, dati: dict) -> list:
    file = sorted(cartella.rglob("*.txt"))
    if not file:
        sys.exit(f"nessun .txt in {cartella}")
    return [detect.analizza(f.read_text(encoding="utf-8"), dati) for f in file]


def riassunto(nome: str, rr: list) -> dict:
    tot = [r.punteggio for r in rr]
    out = {
        "nome": nome,
        "n": len(rr),
        "parole_mediane": statistics.median(r.parole for r in rr),
        "punteggio_mediano": round(statistics.median(tot), 1),
        "passa": round(sum(r.verdetto == "PASSA" for r in rr) / len(rr), 3),
        "dubbio": round(sum(r.verdetto == "DUBBIO" for r in rr) / len(rr), 3),
        "segnalato": round(sum(r.verdetto == "SEGNALATO" for r in rr) / len(rr), 3),
    }
    for c in CONTROLLI:
        out[c] = round(statistics.median(r.controlli[c]["punteggio"] for r in rr), 1)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ia", required=True, type=Path)
    ap.add_argument("--umano", required=True, type=Path, action="append")
    ap.add_argument("--lessico")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    dati = L.carica(a.lessico)

    ia = gruppo(a.ia, dati)
    umani = {p.name: gruppo(p, dati) for p in a.umano}
    righe = [riassunto(f"IA ({a.ia.name})", ia)] + [riassunto(f"umano ({k})", v) for k, v in umani.items()]
    confronti = {}
    for k, v in umani.items():
        confronti[k] = {"auc_totale": round(auc([r.punteggio for r in v], [r.punteggio for r in ia]), 3)}
        for c in CONTROLLI:
            confronti[k][c] = round(
                auc([r.controlli[c]["punteggio"] for r in v], [r.controlli[c]["punteggio"] for r in ia]), 3
            )

    if a.json:
        print(json.dumps({"gruppi": righe, "auc": confronti}, ensure_ascii=False, indent=2))
        return 0

    w = print
    w(f"{'gruppo':<24}{'n':>5}{'parole':>8}{'punt.':>8}{'passa':>8}{'dubbio':>8}{'segnal.':>9}")
    w("-" * 70)
    for r in righe:
        w(f"{r['nome']:<24}{r['n']:>5}{r['parole_mediane']:>8.0f}{r['punteggio_mediano']:>8.1f}"
          f"{r['passa']:>8.0%}{r['dubbio']:>8.0%}{r['segnalato']:>9.0%}")
    w()
    w(f"{'mediane per controllo':<24}" + "".join(f"{c[:8]:>10}" for c in CONTROLLI))
    for r in righe:
        w(f"{r['nome']:<24}" + "".join(f"{r[c]:>10.1f}" for c in CONTROLLI))
    w()
    w(f"{'AUC umano vs IA':<24}{'totale':>10}" + "".join(f"{c[:8]:>10}" for c in CONTROLLI))
    for k, v in confronti.items():
        w(f"{k:<24}{v['auc_totale']:>10.3f}" + "".join(f"{v[c]:>10.3f}" for c in CONTROLLI))
    w()
    w("AUC 0.50 = moneta. 1.00 = separazione perfetta.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
