#!/usr/bin/env python3
"""umanizza · humanize.py — pulisce una bozza italiana in tre passate.

  1. invisibili   caratteri a larghezza zero, spazi strani, BOM, tag Unicode
  2. tipografia   lineette usate come incisi, virgolette curve, puntini
  3. lessico      le voci di slop.json con una sostituzione sicura

Quello che richiede un giudizio (struttura della frase, voci senza
sostituzione) non viene toccato: viene segnalato con --report.

Uso:
  python3 humanize.py bozza.txt                  # testo pulito su stdout
  python3 humanize.py bozza.txt --report         # + ogni modifica e segnalazione su stderr
  python3 humanize.py bozza.txt -o pulito.txt    # scrive su file
  python3 humanize.py bozza.txt --in-place       # sovrascrive (crea bozza.txt.bak)
  cat bozza.txt | python3 humanize.py -          # da stdin
  python3 humanize.py bozza.txt --json           # risultato e report in JSON

Opzioni:
  --solo invisibili,tipografia,lessico   esegue solo alcune passate
  --lineette-dialogo                     converte anche le lineette a inizio riga
  --lessico FILE                         usa un altro slop.json
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lessico as L  # noqa: E402


@dataclass
class Modifica:
    passata: str
    riga: int
    prima: str
    dopo: str
    nota: str = ""


@dataclass
class Segnalazione:
    tipo: str  # "lessico" o "tell"
    riga: int
    estratto: str
    perche: str
    domanda: str = ""  # per chi firma il testo: decide lui se e come riscrivere


@dataclass
class Esito:
    testo: str
    modifiche: list[Modifica] = field(default_factory=list)
    segnalazioni: list[Segnalazione] = field(default_factory=list)


def _riga(testo: str, pos: int) -> int:
    return testo.count("\n", 0, pos) + 1


# --------------------------------------------------------------------------
# Passata 1: invisibili
# --------------------------------------------------------------------------


def passata_invisibili(testo: str, tabella: dict, esito: Esito) -> str:
    trovati = L.invisibili(testo, tabella)
    if not trovati:
        return testo
    per_nome: dict[str, list[int]] = {}
    out = list(testo)
    for i, nome, sost in reversed(trovati):
        out[i] = sost
        per_nome.setdefault(nome, []).append(i)
    for nome, pos in per_nome.items():
        righe = sorted({_riga(testo, p) for p in pos})
        esito.modifiche.append(
            Modifica("invisibili", righe[0], f"{len(pos)}× {nome}", "rimosso", "righe " + ", ".join(map(str, righe[:10])))
        )
    return "".join(out)


# --------------------------------------------------------------------------
# Passata 2: tipografia
# --------------------------------------------------------------------------


def _sostituisci_fuori_zone(testo: str, rx: re.Pattern, fn, passata: str, esito: Esito, nota: str = "") -> str:
    zone = L.zone_protette(testo)
    pezzi, ultimo = [], 0
    for m in rx.finditer(testo):
        if L._in_zona(m.span(), zone):
            continue
        nuovo = fn(m)
        if nuovo is None or nuovo == m.group(0):
            continue
        pezzi.append(testo[ultimo : m.start()])
        pezzi.append(nuovo)
        esito.modifiche.append(Modifica(passata, _riga(testo, m.start()), m.group(0), nuovo, nota))
        ultimo = m.end()
    pezzi.append(testo[ultimo:])
    return "".join(pezzi)


_MESI = r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"


def passata_tipografia(testo: str, esito: Esito, dialogo: bool = False) -> str:
    def riga_di_dialogo(pos: int) -> bool:
        inizio = testo.rfind("\n", 0, pos) + 1
        return bool(re.match(r"[ \t]*[—–]", testo[inizio:]))

    # Lineetta usata come inciso → virgola. Tutte le lineette di una riga di dialogo
    # ("— A casa — rispose lei — perché è tardi") restano: è italiano corretto.
    def intestazione(pos: int) -> bool:
        # «Milano, 12 marzo 2026 — L'azienda…», «[Città], [data] — …»: la lineetta della data di un comunicato resta.
        testa = testo[testo.rfind("\n", 0, pos) + 1:pos].strip().strip("*_ ")
        return (testa.count(",") == 1 and len(testa.split()) <= 8 and "—" not in testa and "–" not in testa
                and bool(re.search(r"\d|\[|" + _MESI, testa, re.IGNORECASE)))

    def lineetta(m: re.Match) -> str | None:
        if riga_di_dialogo(m.start()) and not dialogo:
            return None
        if intestazione(m.start()):
            return None
        if m.group(0).strip() == "–" and not (m.group(0).startswith((" ", "\t")) and m.group(0).endswith((" ", "\t"))):
            return None  # "Roma–Milano": trattino di collegamento, non un inciso
        prima = m.string[: m.start()].rstrip()
        dopo = m.string[m.end() :].lstrip()
        if not prima or prima[-1] in ",;:(\n":
            return " " if prima else ""
        if dopo[:1] in (".", ",", ";", ":", "!", "?", ")", ""):
            return ""
        return ", "

    # Intervalli numerici 10–20 → 10-20
    testo = _sostituisci_fuori_zone(testo, re.compile(r"(?<=\d)\s?[–—]\s?(?=\d)"), lambda m: "-", "tipografia", esito, "intervallo")
    testo = _sostituisci_fuori_zone(testo, re.compile(r"[ \t]*[—–][ \t]*"), lineetta, "tipografia", esito, "lineetta come inciso")
    # Virgolette e apostrofi curvi → dritti. « » restano: sono italiane.
    tab = {"“": '"', "”": '"', "„": '"', "‟": '"', "‘": "'", "’": "'", "‚": "'", "‛": "'", "′": "'", "″": '"'}
    zone = L.zone_protette(testo)
    pos = [i for i, c in enumerate(testo) if c in tab and not L._in_zona((i, i + 1), zone)]
    if pos:
        lista = list(testo)
        for i in pos:
            lista[i] = tab[lista[i]]
        testo = "".join(lista)
        esito.modifiche.append(Modifica("tipografia", 0, f"{len(pos)}× virgolette/apostrofi curvi", "dritti"))
    testo = _sostituisci_fuori_zone(testo, re.compile("…"), lambda m: "...", "tipografia", esito, "puntini")
    return testo


# --------------------------------------------------------------------------
# Passata 3: lessico
# --------------------------------------------------------------------------

_INIZIO_FRASE = re.compile(
    r"(?:(?:^|\n)[ \t]*(?:(?:#{1,6}|>|[-*+•]|\d+[.)])[ \t]+)?|[.!?:][ \t]+|[\"«(][ \t]*)$"
)


def _maiuscola(s: str) -> str:
    """Prima lettera maiuscola, ma non tocca iPhone, eBay, npm, 3D."""
    m = re.search(r"[^\W\d_]", s)
    if not m or s[: m.start()].strip(" \t\"«(*_"):
        return s
    parola = re.match(r"\w+", s[m.start():]).group(0)
    if any(c.isupper() for c in parola[1:]):
        return s
    i = m.start()
    return s[:i] + s[i].upper() + s[i + 1 :]


def _cancellazione_sicura(testo: str, m: re.Match, a_inizio: bool) -> bool:
    """Si cancella solo dove la frase resta in piedi da sola.

    - a inizio frase, se la voce finisce con una virgola o con "che"
      ("In conclusione, X" → "X"; "È importante sottolineare che X" → "X")
    - come inciso tra due virgole ("Il progetto, in conclusione, funziona")
    Mai dentro un grassetto, mai se la riga resterebbe senza parole.
    """
    voce = m.group(0).rstrip()
    prima = testo[: m.start()]
    if re.search(r"\bnon\s+$", prima, re.I) or re.search(r"(\*\*|__)$", prima):
        return False
    inizio_riga = testo.rfind("\n", 0, m.start()) + 1
    fine_riga = testo.find("\n", m.end())
    resto = testo[inizio_riga : m.start()] + testo[m.end() : fine_riga if fine_riga >= 0 else len(testo)]
    if not re.search(r"[^\W_]", resto):
        return False
    if a_inizio and (voce.endswith(",") or voce.lower().endswith(" che")):
        return True
    return voce.endswith(",") and bool(re.search(r",[ \t]*$", prima))


def passata_lessico(testo: str, voci: list, esito: Esito) -> str:
    for v in voci:
        if v.solo_segnala:
            continue
        zone = L.zone_protette(testo)
        pezzi, ultimo, da_maiuscolare = [], 0, False
        for m in v.rx.finditer(testo):
            if m.end() == m.start() or L._in_zona(m.span(), zone):
                continue
            originale = m.group(0)
            lettere = [c for c in originale if c.isalpha()]
            if len(lettere) > 1 and all(c.isupper() for c in lettere):
                continue  # TESTO IN MAIUSCOLO: lo lasciamo a chi scrive
            prima = testo[: m.start()]
            a_inizio = m.start() == 0 or bool(_INIZIO_FRASE.search(prima))
            nuovo = v.sostituisci
            if nuovo == "" and not _cancellazione_sicura(testo, m, a_inizio):
                continue  # resta tra le segnalazioni
            if nuovo and originale[:1].isupper():
                nuovo = _maiuscola(nuovo)
            pezzi.append(testo[ultimo : m.start()])
            if nuovo == "" and not a_inizio:
                # inciso: "Il progetto, in conclusione, funziona" → "Il progetto funziona"
                pezzi[-1] = re.sub(r",[ \t]*$", " ", pezzi[-1])
            if da_maiuscolare:
                pezzi[-1] = _maiuscola(pezzi[-1])
                da_maiuscolare = False
            pezzi.append(nuovo)
            if nuovo == "" and a_inizio and originale[:1].isupper():
                da_maiuscolare = True
            esito.modifiche.append(Modifica("lessico", _riga(testo, m.start()), originale, nuovo or "(tolto)", v.nota or v.cat))
            ultimo = m.end()
            if nuovo == "" and a_inizio:
                while ultimo < len(testo) and testo[ultimo] in " \t":
                    ultimo += 1
        coda = testo[ultimo:]
        if da_maiuscolare:
            coda = _maiuscola(coda)
        pezzi.append(coda)
        testo = "".join(pezzi)
    return testo


# --------------------------------------------------------------------------
# Rifinitura: la punteggiatura orfana che lasciano le passate.
# Gira solo sulle righe che le passate hanno cambiato.
# --------------------------------------------------------------------------


def rifinisci_riga(riga: str) -> str:
    zone_txt = []

    def proteggi(m: re.Match) -> str:
        zone_txt.append(m.group(0))
        return f"\u0001{len(zone_txt) - 1}\u0001"

    t = L._RX_PROTETTE.sub(proteggi, riga)
    t = re.sub(r"(?<=[^\W_])[ \t]+([,;])(?=\s|$)", r"\1", t)  # "parola ," → "parola,"
    t = re.sub(r"(?<=[^\W_])[ \t]+\.(?=\s|$)", ".", t)  # "parola ." → "parola."
    t = re.sub(r",[ \t]*,", ",", t)  # virgole doppie
    t = re.sub(r",[ \t]*([.;!?])(?=\s|$)", r"\1", t)  # virgola orfana prima di un punto
    t = re.sub(r"^([ \t]*(?:(?:#{1,6}|>|[-*+•]|\d+[.)])[ \t]+)?)[,;][ \t]*", r"\1", t)  # riga che inizia con una virgola
    t = re.sub(r"(?<=\S)[ \t]{2,}(?=\S)", " ", t)  # spazi doppi (non l'indentazione)
    t = t.rstrip(" \t")
    return re.sub(r"\u0001(\d+)\u0001", lambda m: zone_txt[int(m.group(1))], t)


def rifinisci(prima: str, dopo: str) -> str:
    rp, rd = prima.split("\n"), dopo.split("\n")
    if len(rp) != len(rd):
        return "\n".join(rifinisci_riga(r) for r in rd)
    out = []
    for a, b in zip(rp, rd):
        if a == b:
            out.append(b)
            continue
        r = rifinisci_riga(b)
        if r.strip() == "" and a.strip() != "":
            continue  # riga svuotata da una cancellazione: via
        out.append(r)
    t = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", t) if "\n\n\n" not in prima else t


# --------------------------------------------------------------------------
# Orchestrazione
# --------------------------------------------------------------------------


def umanizza(testo: str, dati: dict, passate=("invisibili", "tipografia", "lessico"), dialogo=False, genere=None) -> Esito:
    esito = Esito(testo="")
    t = L.normalizza_nfc(testo)
    if "invisibili" in passate:
        t = passata_invisibili(t, dati["invisibili"], esito)
    base = t
    if "tipografia" in passate:
        t = passata_tipografia(t, esito, dialogo=dialogo)
    if "lessico" in passate:
        t = passata_lessico(t, dati["voci"], esito)
    if t != base:
        t = rifinisci(base, t)
    esito.modifiche.sort(key=lambda m: (m.riga == 0, m.riga))
    # Segnalazioni: ciò che resta e richiede giudizio.
    for c in L.trova_lessico(t, dati["voci"]):
        perche = c.voce.perche or ("da riscrivere a mano" if c.voce.solo_segnala else "")
        if c.voce.solo_segnala or c.voce.peso < 1:
            esito.segnalazioni.append(Segnalazione("lessico", _riga(t, c.inizio), c.testo, f"[{c.voce.cat}] {perche}".strip(),
                                                   dati.get("domande", {}).get(c.voce.cat, "")))
    for tl in L.trova_tell(t, accademico=genere == "accademico"):
        info = dati["tell"].get(tl.id, {})
        esito.segnalazioni.append(Segnalazione("tell", tl.riga, tl.estratto, f"{info.get('nome', tl.id)}: {info.get('perche', '')}",
                                               info.get("domanda", "")))
    esito.segnalazioni.sort(key=lambda x: (x.riga == 0, x.riga))
    esito.testo = t
    return esito


def stampa_report(esito: Esito, out=sys.stderr) -> None:
    w = lambda s="": print(s, file=out)  # noqa: E731
    w("=" * 72)
    w(f"UMANIZZA · {len(esito.modifiche)} modifiche · {len(esito.segnalazioni)} segnalazioni")
    w("=" * 72)
    if esito.modifiche:
        w("MODIFICATO")
        for m in esito.modifiche:
            r = f"r{m.riga:<3}" if m.riga else "    "
            nota = f"  ({m.nota})" if m.nota else ""
            w(f"  {r} {m.passata:<10} {m.prima!r} → {m.dopo!r}{nota}")
    if esito.segnalazioni:
        w()
        w("DA RISCRIVERE A MANO (non toccato)")
        for s in esito.segnalazioni:
            r = f"r{s.riga:<3}" if s.riga else "    "
            w(f"  {r} {s.tipo:<8} «{s.estratto}»")
            if s.perche:
                w(f"       {'':8} ↳ {s.perche}")
            if s.domanda:
                w(f"       {'':8} ? {s.domanda}")
    if not esito.modifiche and not esito.segnalazioni:
        w("Niente da pulire.")
    w("-" * 72)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Pulisce una bozza italiana dallo slop.")
    ap.add_argument("file", help="file di testo, oppure - per stdin")
    ap.add_argument("-o", "--out", help="scrivi il testo pulito qui")
    ap.add_argument("--in-place", action="store_true", help="sovrascrive il file (con backup .bak)")
    ap.add_argument("--report", action="store_true", help="mostra modifiche e segnalazioni su stderr")
    ap.add_argument("--json", action="store_true", help="stampa testo e report in JSON")
    ap.add_argument("--solo", default="invisibili,tipografia,lessico", help="passate da eseguire")
    ap.add_argument("--lineette-dialogo", action="store_true", help="converte anche la lineetta del dialogo")
    ap.add_argument("--lessico", help="percorso di un slop.json alternativo")
    ap.add_argument("--genere", choices=["generico", "accademico"], default="generico",
                    help="accademico: gli elenchi di nomi, opere e date non vengono segnalati come triadi")
    a = ap.parse_args(argv)

    try:
        testo = sys.stdin.read() if a.file == "-" else Path(a.file).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        print(f"humanize: non riesco a leggere {a.file}: {e}", file=sys.stderr)
        return 2
    dati = L.carica(a.lessico)
    passate = tuple(p.strip() for p in a.solo.split(",") if p.strip())
    ignote = set(passate) - {"invisibili", "tipografia", "lessico"}
    if ignote:
        ap.error("passate sconosciute: " + ", ".join(sorted(ignote)))
    esito = umanizza(testo, dati, passate, a.lineette_dialogo, a.genere)

    if a.json:
        print(json.dumps({"testo": esito.testo, "modifiche": [asdict(m) for m in esito.modifiche],
                          "segnalazioni": [asdict(s) for s in esito.segnalazioni]}, ensure_ascii=False, indent=2))
        return 0
    if a.report:
        stampa_report(esito)
    if a.in_place:
        if a.file == "-":
            ap.error("--in-place richiede un file")
        shutil.copyfile(a.file, a.file + ".bak")
        Path(a.file).write_text(esito.testo, encoding="utf-8")
    elif a.out:
        Path(a.out).write_text(esito.testo, encoding="utf-8")
    else:
        sys.stdout.write(esito.testo)
        if not esito.testo.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
