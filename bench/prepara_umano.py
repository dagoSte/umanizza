#!/usr/bin/env python3
"""Scarica italiano scritto da persone, prima dei modelli linguistici, e lo taglia in campioni.

Fonti (Universal Dependencies, licenze CC BY-NC-SA: per questo non sono nel repo):
  social  PoSTWITA + TWITTIRO   tweet italiani 2011-2015
  prosa   ISDT + VIT            giornali, Wikipedia, testi normativi (anni 1990-2000)

Uso:
  python3 prepara_umano.py corpus/umano            # scarica e scrive i campioni
  python3 prepara_umano.py corpus/umano --locale DIR_CON_I_CONLLU
  python3 prepara_umano.py corpus/umano --dividi   # campioni alterni in dev/ e test/ (come nel README)

Ogni campione diventa un file .txt:
  social: tweet consecutivi uniti fino ad almeno 40 parole (un tweet = una riga)
  prosa:  frasi consecutive dello stesso documento fino a circa 150 parole
"""
from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

BASE = "https://raw.githubusercontent.com/UniversalDependencies/{repo}/master/{file}"
FONTI = {
    "social": [
        ("UD_Italian-PoSTWITA", "it_postwita-ud-dev.conllu"),
        ("UD_Italian-PoSTWITA", "it_postwita-ud-test.conllu"),
        ("UD_Italian-TWITTIRO", "it_twittiro-ud-test.conllu"),
    ],
    "prosa": [
        ("UD_Italian-ISDT", "it_isdt-ud-dev.conllu"),
        ("UD_Italian-ISDT", "it_isdt-ud-test.conllu"),
        ("UD_Italian-VIT", "it_vit-ud-test.conllu"),
    ],
}


def frasi_conllu(testo: str) -> list[tuple[str, str]]:
    """(sent_id, testo) per ogni frase."""
    out, sid = [], ""
    for riga in testo.splitlines():
        if riga.startswith("# sent_id"):
            sid = riga.split("=", 1)[1].strip()
        elif riga.startswith("# text ="):
            out.append((sid, riga.split("=", 1)[1].strip()))
    return out


def _doc(sid: str) -> str:
    # isst_tanl-14 → isst_tanl ; VIT-4751 → VIT ; i numeri consecutivi restano nello stesso blocco
    return re.sub(r"[-_]?\d+$", "", sid)


def _num(sid: str) -> int:
    m = re.search(r"(\d+)$", sid)
    return int(m.group(1)) if m else -1


def campioni(frasi: list[tuple[str, str]], minimo: int, massimo: int, sep: str, salto_max: int) -> list[str]:
    out, buf, n, prec = [], [], 0, None
    for sid, t in frasi:
        stacco = prec is not None and (_doc(sid) != _doc(prec) or _num(sid) - _num(prec) > salto_max)
        if buf and (stacco or n >= massimo):
            if n >= minimo:
                out.append(sep.join(buf))
            buf, n = [], 0
        buf.append(t)
        n += len(t.split())
        prec = sid
        if n >= massimo:
            out.append(sep.join(buf))
            buf, n = [], 0
    if buf and n >= minimo:
        out.append(sep.join(buf))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dest")
    ap.add_argument("--locale", help="cartella con i .conllu già scaricati")
    ap.add_argument("--dividi", action="store_true", help="alterna i campioni tra dev/ e test/")
    a = ap.parse_args()
    dest = Path(a.dest)
    for genere, fonti in FONTI.items():
        cartelle = [dest / "dev" / genere, dest / "test" / genere] if a.dividi else [dest / genere]
        for c in cartelle:
            c.mkdir(parents=True, exist_ok=True)
        tutte = []
        for repo, nome in fonti:
            if a.locale and (Path(a.locale) / nome).exists():
                testo = (Path(a.locale) / nome).read_text(encoding="utf-8")
            else:
                url = BASE.format(repo=repo, file=nome)
                print("scarico", url, file=sys.stderr)
                testo = urllib.request.urlopen(url, timeout=60).read().decode("utf-8")
            tutte.append(frasi_conllu(testo))
        k = 0
        for frasi in tutte:
            if genere == "social":
                # Nei tweet gli id sono numerici e "vicini" = stesso tweet o tweet adiacenti.
                cc = campioni(frasi, 40, 90, "\n", salto_max=10**9)
            else:
                cc = campioni(frasi, 80, 170, " ", salto_max=40)
            for c in cc:
                k += 1
                cartella = cartelle[(k - 1) % len(cartelle)]
                (cartella / f"{genere}_{k:04d}.txt").write_text(c + "\n", encoding="utf-8")
        print(f"{genere}: {k} campioni in {', '.join(map(str, cartelle))}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
