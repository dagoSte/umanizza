#!/usr/bin/env python3
"""umanizza · indice.py — indice di affidabilità da 0,00 a 10,00, calcolato dai risultati del benchmark.

    python3 bench/indice.py            # stampa l'indice e le sue componenti
    python3 bench/indice.py --json

Formula dichiarata (versione 1, fissata prima del calcolo, 26/11/2026). Ogni componente va da 0 a 1:

  Riconoscimento (metà dell'indice)
    D  separazione   media di (AUC − 0,5) / 0,5 su 12 confronti: prosa e tweet della metà di test UD e secondo
                     campione web, contro Claude Sonnet e Haiku, GPT, Claude Opus e Claude Fable.   peso 0,30
    S  falsi allarmi quota di testi umani (tweet, prosa, web) che NON finiscono SEGNALATO.            peso 0,10
    C  copertura     quota di generi misurati (tweet, prosa, web, accademico) con AUC media ≥ 0,80.   peso 0,10
  Riscrittura (l'altra metà)
    P  pulizia       1 − sostituzioni sbagliate / sostituzioni fatte sui 444 testi umani.             peso 0,15
    F  fedeltà       quota di riscritture della lettura alla cieca senza numeri, nomi o citazioni
                     persi o aggiunti.                                                                  peso 0,15
    L  leggibilità   preferenza per il testo riscritto nelle 40 risposte della prima lettura alla
                     cieca (pari = mezzo), riportata da [0,5, 1] a [0, 1]; sotto 0,5 vale 0.          peso 0,20

  Indice = 10 × (0,30 D + 0,10 S + 0,10 C + 0,15 P + 0,15 F + 0,20 L)

Solo dati di verifica: niente metà di sviluppo, niente primo campione web (servito a trovare il difetto di IMPRONTA).
La componente L usa la lettura alla cieca della versione attuale della skill: la prima, perché le regole provate
nella seconda e nella terza (bench/lettura-cieca-2, -3) non sono entrate. Regola fissata prima della terza prova.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
RIS = RADICE / "bench" / "risultati"
sys.path.insert(0, str(RADICE / "skills" / "umanizza"))
import lessico as L  # noqa: E402

PESI = {"D": 0.30, "S": 0.10, "C": 0.10, "P": 0.15, "F": 0.15, "L": 0.20}
MODELLI_UD = ["test", "gpt", "opus", "fable"]          # contro la metà di test UD (tweet e prosa)
MODELLI_WEB = ["web2_claude", "web2_gpt", "opus_web2", "fable_web2"]  # contro il secondo campione web


def _j(nome: str) -> dict:
    return json.loads((RIS / f"{nome}.json").read_text(encoding="utf-8"))


def _norm(auc: float) -> float:
    return max(0.0, (auc - 0.5) / 0.5)


def _coppie(cartella: Path) -> list[dict]:
    md = (cartella / "coppie.md").read_text(encoding="utf-8")
    out = []
    for b in re.split(r"\n## Coppia ", md)[1:]:
        corpo = b.split("\n", 1)[1]
        a, resto = corpo.split("### Testo A\n\n", 1)[1].split("\n\n### Testo B\n\n", 1)
        out.append({"A": a.strip(), "B": resto.split("\n\n---", 1)[0].strip()})
    return out


def calcola() -> dict:
    auc_ud = {m: _j(m)["auc"] for m in MODELLI_UD}
    auc_web = {m: _j(m)["auc"]["tutti"]["auc_totale"] for m in MODELLI_WEB}
    confronti = [auc_ud[m][g]["auc_totale"] for m in MODELLI_UD for g in ("prosa", "social")] + list(auc_web.values())
    D = sum(_norm(a) for a in confronti) / len(confronti)

    umani = [g for g in _j("test")["gruppi"] if g["nome"].startswith("umano")]
    umani += [g for g in _j("web2_gpt")["gruppi"] if g["nome"].startswith("umano")]
    S = 1 - sum(g["segnalato"] * g["n"] for g in umani) / sum(g["n"] for g in umani)

    generi = {
        "tweet": sum(auc_ud[m]["social"]["auc_totale"] for m in MODELLI_UD) / 4,
        "prosa": sum(auc_ud[m]["prosa"]["auc_totale"] for m in MODELLI_UD) / 4,
        "web": sum(auc_web.values()) / 4,
        "accademico": _j("accademico")["auc_totale"],
    }
    C = sum(v >= 0.80 for v in generi.values()) / len(generi)

    pul = _j("pulizia")
    P = 1 - pul["sbagliate"] / max(pul["sostituzioni"], 1)

    lc = RADICE / "bench" / "lettura-cieca"
    chiave = json.loads((lc / "chiave.json").read_text(encoding="utf-8"))
    coppie = _coppie(lc)
    fedeli = 0
    for c, k in zip(coppie, chiave):
        orig, risc = (c["A"], c["B"]) if k["A"] == "originale" else (c["B"], c["A"])
        f = L.confronta_fatti(orig, risc)
        fedeli += not f["persi"] and not f["nuovi"]
    F = fedeli / len(coppie)

    punti = n = 0
    for nome in ("claude", "gpt"):
        risposte = json.loads((lc / "risposte" / f"{nome}.json").read_text(encoding="utf-8"))
        for r in risposte:
            k = chiave[r["coppia"] - 1]
            punti += 0.5 if r["meglio"] == "pari" else float((r["meglio"] == "A") == (k["A"] == "riscritto"))
            n += 1
    Lg = _norm(punti / n)

    comp = {"D": D, "S": S, "C": C, "P": P, "F": F, "L": Lg}
    indice = 10 * sum(PESI[k] * v for k, v in comp.items())
    return {"indice": round(indice, 2), "componenti": {k: round(v, 3) for k, v in comp.items()}, "pesi": PESI,
            "dettagli": {"confronti_auc": [round(a, 3) for a in confronti], "generi": {k: round(v, 3) for k, v in generi.items()},
                         "testi_umani": sum(g["n"] for g in umani), "riscritture_fedeli": f"{fedeli}/{len(coppie)}",
                         "preferenza_riscritto": f"{punti}/{n}"}}


def formatta(x: float) -> str:
    return f"{x:.2f}".replace(".", ",")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    r = calcola()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0
    nomi = {"D": "riconoscimento", "S": "falsi allarmi evitati", "C": "copertura dei generi", "P": "pulizia sicura",
            "F": "fedeltà ai fatti", "L": "leggibilità della riscrittura"}
    print(f"Indice di affidabilità: {formatta(r['indice'])} / 10")
    for k, v in r["componenti"].items():
        print(f"  {k} {nomi[k]:30} {formatta(v)}  × {formatta(PESI[k])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
