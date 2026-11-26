#!/usr/bin/env python3
"""umanizza · detect.py — punteggio umano di un testo italiano, cinque controlli.

  RITMO        variazione della lunghezza delle frasi (le persone alternano)
  CONCRETEZZA  numeri, nomi, date, unità, codice: cose verificabili
  SLOP         voci del lessico per 100 parole, pesate
  IMPRONTA     caratteri invisibili, lineette come incisi, tipografia da generatore
  VOCE         tell strutturali (non è solo X è Y, triadi, Title Case, ...)

Sono euristiche locali, non un detector commerciale. Vedi README.

Uso:
  python3 detect.py testo.txt                 # pannello
  python3 detect.py prima.txt dopo.txt        # confronto con delta
  python3 detect.py testo.txt --json          # numeri in JSON
  python3 detect.py testo.txt --dettagli      # elenca ogni voce e ogni tell trovati
  cat testo.txt | python3 detect.py -
Esce con codice 1 se il verdetto è SEGNALATO (utile in CI o negli hook), 2 se non legge il file.
Sotto le 15 parole, o se il testo non sembra italiano, il verdetto è N/D.
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lessico as L  # noqa: E402

PESI = {"ritmo": 0.10, "concretezza": 0.25, "slop": 0.25, "impronta": 0.10, "voce": 0.30}
SOGLIA_PASSA = 85.0  # tarata sul dev: 93% dei testi umani passa
SOGLIA_SEGNALATO = 70.0  # tarata sul dev: 0% dei testi umani sotto

_NUMERI_PAROLE = (
    r"due|tre|quattro|cinque|sei|sette|otto|nove|dieci|undici|dodici|tredici|quattordici|quindici|sedici|"
    r"diciassette|diciotto|diciannove|venti|ventuno|trenta|quaranta|cinquanta|sessanta|settanta|ottanta|novanta|"
    r"cento|duecento|trecento|cinquecento|mille|duemila|tremila|diecimila|centomila|milione|milioni|miliardo|miliardi|"
    r"mezzo|mezza|dozzina|decina|decine|centinaio|centinaia|migliaia|zero"
)
_MESI = r"gennaio|febbraio|marzo|aprile|maggio|giugno|luglio|agosto|settembre|ottobre|novembre|dicembre"
_GIORNI = r"lunedì|martedì|mercoledì|giovedì|venerdì|sabato|domenica|ieri|stamattina|stasera|stanotte"
_UNITA = (
    r"€|\$|£|%|euro|dollari|km|kg|gb|mb|tb|kb|ms|ghz|mhz|mq"
)
_RX_CONCRETO = re.compile(
    rf"\d[\d.,:/]*|(?<!\w)(?:{_NUMERI_PAROLE}|{_MESI}|{_GIORNI})(?!\w)|(?<!\w)(?:{_UNITA})(?!\w)|`[^`]+`|https?://\S+|(?<!\w)@\w+",
    re.IGNORECASE,
)
# Parole maiuscole a metà frase che NON sono nomi propri (articoli dopo virgolette ecc. si filtrano a parte).
_NON_NOMI = {"Io", "Tu", "Lei", "Noi", "Voi", "Loro", "Ok", "Ecco", "Grazie", "Ciao", "No", "Sì", "Si", "E", "Ma", "Il", "La", "Le", "Lo", "Gli", "Un", "Una", "Non", "Che", "Per"}


@dataclass
class Controllo:
    nome: str
    punteggio: float
    dettaglio: str
    disponibile: bool = True


@dataclass
class Risultato:
    parole: int
    frasi: int
    controlli: dict
    punteggio: float
    verdetto: str
    ostacoli: list = field(default_factory=list)
    voci: list = field(default_factory=list)
    tell: list = field(default_factory=list)
    genere: str = "generico"


_ACRONIMI_COMUNI = {"OK", "NON", "CHE", "PER", "IL", "LA", "LE", "GLI", "UN", "UNA", "MA", "SE", "NO", "SI", "SÌ"}


def _nomi_propri(frase: str) -> int:
    """Parole maiuscole a metà frase (nomi, prodotti, sigle). Le frasi urlate non contano."""
    pp = L.parole(frase)
    if sum(p.isupper() for p in pp) > len(pp) / 2:
        return 0
    n = 0
    for p in pp[1:]:
        if p.isupper():
            if 2 <= len(p) <= 6 and p not in _ACRONIMI_COMUNI:
                n += 1  # sigla: MCP, DGX, API
        elif p[:1].isupper() and p not in _NON_NOMI:
            n += 1
    return n


def c_ritmo(ff: list[str]) -> Controllo:
    lun = [len(L.parole(f)) for f in ff]
    if len(lun) < 4:
        return Controllo("RITMO", 75.0, f"{len(lun)} frasi: troppo poche per misurare", False)
    media = statistics.mean(lun)
    cv = statistics.pstdev(lun) / max(1e-9, media)
    punteggio = min(100.0, cv / 0.55 * 100)
    return Controllo("RITMO", punteggio, f"variazione {cv:.2f} · media {media:.0f} parole/frase")


def c_concretezza(testo: str, ff: list[str], n_parole: int, accademico: bool = False) -> Controllo:
    if accademico:  # le citazioni dicono chi è stato citato, non quanto è concreta la prosa; il denominatore resta
        testo = L.togli_apparato(testo)
        ff = L.frasi(testo)
    marcatori = len(_RX_CONCRETO.findall(L._togli_codice(testo))) + sum(_nomi_propri(f) for f in ff)
    tasso = marcatori * 100 / max(n_parole, 30)
    punteggio = min(100.0, tasso / 7.0 * 100)
    return Controllo("CONCRETEZZA", punteggio, f"{tasso:.1f} elementi concreti ogni 100 parole")


def c_slop(colpi: list, n_parole: int) -> Controllo:
    colpi = [c for c in colpi if c.voce.conta]  # voci che non distinguono ("slop": false) non contano
    peso = sum(c.voce.peso for c in colpi)
    tasso = peso * 100 / max(n_parole, 60)
    punteggio = max(0.0, 100 - tasso * 22)
    forti = sum(1 for c in colpi if c.voce.peso >= 1)
    return Controllo("SLOP", punteggio, f"{len(colpi)} voci ({forti} forti) · {tasso:.1f} per 100 parole")


def c_impronta(testo: str, tabella: dict) -> tuple[Controllo, list[str]]:
    ostacoli = []
    inv = L.invisibili(testo, tabella)
    # Spazi indivisibili da soli sono comuni (Word, tastiere francesi): pesano meno.
    gravi = [x for x in inv if x[2] == ""]
    lievi = [x for x in inv if x[2] != ""]
    lin = L.lineette(testo)
    curve = len(re.findall(r"[“”„]", L._togli_codice(testo)))
    p = 100.0
    if gravi:
        p -= 45
        ostacoli.append(f"{len(gravi)} caratteri invisibili a larghezza zero: nessuna tastiera li produce.")
    if lievi:
        p -= min(10, 2 * len(lievi))
    # Lineette: si contano ma non pesano. Misurato nella 1.6.0: le usa il 28% dei testi web umani e quasi nessun
    # testo generato (1 su 90). Virgolette curve e "…" non pesano: li producono iPhone, Word e i social.
    parti = [f"{len(lin)} lineette come inciso", f"{len(gravi)} invisibili"]
    if lievi:
        parti.append(f"{len(lievi)} spazi speciali")
    if curve:
        parti.append(f"{curve} virgolette curve")
    return Controllo("IMPRONTA", max(0.0, p), " · ".join(parti)), ostacoli


def c_voce(tell: list, n_parole: int) -> Controllo:
    peso = sum(t.peso for t in tell if t.id != "ritmo-uniforme")
    penalita = 28 * peso * 100 / max(n_parole, 100)
    punteggio = max(0.0, 100 - penalita)
    tipi = sorted({t.id for t in tell})
    return Controllo("VOCE", punteggio, f"{len(tell)} tell strutturali" + (f": {', '.join(tipi[:4])}" if tipi else ""))


_IT = set("il lo la gli le di che e è per non un una del della in con sono si ma come anche più questo".split())
_EN = set("the and of to is in that it for you with on this are be not your but as".split())


def _sembra_italiano(pp: list[str]) -> bool:
    low = [p.lower() for p in pp]
    it = sum(p in _IT for p in low)
    en = sum(p in _EN for p in low)
    return it >= en


def carica_soglie(path: str | Path | None = None, piattaforma: str | None = None) -> dict | None:
    """Soglie personali salvate da taratura.py applica. None se non c'è taratura."""
    p = Path(path) if path else Path.home() / ".claude" / "umanizza" / "taratura.json"
    if not p.exists():
        return None
    t = json.loads(p.read_text(encoding="utf-8"))
    sel = t.get("per_piattaforma", {}).get(piattaforma) if piattaforma else None
    sel = sel or t
    return {"passa": float(sel["soglia_passa"]), "segnalato": float(sel["soglia_segnalato"]),
            "origine": f"taratura personale{' (' + piattaforma + ')' if piattaforma and sel is not t else ''}"}


def analizza(testo: str, dati: dict, soglie: dict | None = None, genere: str | None = None) -> Risultato:
    accademico = genere == "accademico"
    testo = L.normalizza_nfc(testo)
    ff = L.frasi(testo)
    n_parole = len(L.parole(L._togli_codice(testo)))
    colpi = L.trova_lessico(testo, dati["voci"])
    tell = L.trova_tell(testo, accademico=accademico)
    impronta, ostacoli = c_impronta(testo, dati["invisibili"])
    controlli = {
        "ritmo": c_ritmo(ff),
        "concretezza": c_concretezza(testo, ff, n_parole, accademico),
        "slop": c_slop(colpi, n_parole),
        "impronta": impronta,
        "voce": c_voce(tell, n_parole),
    }
    totale = sum(PESI[k] * c.punteggio for k, c in controlli.items())
    if ostacoli:
        totale = min(totale, 60.0)
    passa = soglie["passa"] if soglie else SOGLIA_PASSA
    segnalato = soglie["segnalato"] if soglie else SOGLIA_SEGNALATO
    verdetto = "PASSA" if totale >= passa else ("DUBBIO" if totale >= segnalato else "SEGNALATO")
    if n_parole < 15:
        ostacoli.append(f"Solo {n_parole} parole: troppo poche per un verdetto.")
        verdetto = "N/D"
    elif not _sembra_italiano(L.parole(testo)):
        ostacoli.append("Il testo non sembra italiano: lessico e controlli sono tarati sull'italiano.")
        verdetto = "N/D"
    return Risultato(
        parole=n_parole,
        frasi=len(ff),
        controlli={k: asdict(c) for k, c in controlli.items()},
        punteggio=round(totale, 1),
        verdetto=verdetto,
        ostacoli=ostacoli,
        voci=[{"riga": testo.count("\n", 0, c.inizio) + 1, "testo": c.testo, "cat": c.voce.cat, "peso": c.voce.peso} for c in colpi],
        tell=[asdict(t) for t in tell],
        genere="accademico" if accademico else "generico",
    )


# --------------------------------------------------------------------------
# Mappa: le frasi da riscrivere a mano per prime. Non entra nel punteggio e non riscrive nulla.
# Quattro costrutti più frequenti nei modelli istruiti (in inglese; per l'italiano è un'ipotesi da tarare).
# --------------------------------------------------------------------------

_RX_GERUNDIO = re.compile(
    r",\s+(?:non\s+)?([a-zàèéìòù]+(?:ando|endo)(?:lo|la|li|le|ne|si|ci|vi|mi|ti|gli|glielo|gliela)?)\b", re.I
)
_NON_GERUNDI = {"quando", "orrendo", "stupendo", "tremendo", "reverendo", "dividendo", "addendo", "nefando",
                "comando", "contrabbando", "bando", "mando"}
_RX_NOMINALIZZAZIONE = re.compile(r"\b[a-zàèéìòù]{4,}(?:zione|zioni|mento|menti|ità|enza|enze|anza|anze)\b")  # minuscole: i nomi propri no
_NON_NOMINALIZZAZIONI = {
    "momento", "momenti", "documento", "documenti", "elemento", "elementi", "argomento", "argomenti",
    "appartamento", "appartamenti", "strumento", "strumenti", "monumento", "monumenti", "parlamento", "testamento",
    "frammento", "frammenti", "sentimento", "sentimenti", "complimenti", "pavimento", "alimento", "alimenti",
    "segmento", "segmenti", "università", "nazione", "nazioni", "stazione", "stazioni", "lezione", "lezioni",
    "abbastanza", "finanza", "finanze",
}
_RX_CONNETTIVO_APERTURA = re.compile(
    r"^(?:inoltre|tuttavia|pertanto|infatti|dunque|quindi|peraltro|del resto|in conclusione|in sintesi|insomma|"
    r"ciononostante|nonostante ciò|di conseguenza|in definitiva|allo stesso tempo|in questo senso|in altre parole|"
    r"in particolare|in effetti|d['’]altra parte|al contrario|in realtà)\b",
    re.I,
)
_RX_IMPERSONALE = re.compile(
    r"\b(?:[èÈ]|E['’])\s+(?:importante|fondamentale|cruciale|essenziale|necessario|interessante|utile|bene|opportuno|"
    r"evidente|chiaro|significativo|innegabile|indubbio|curioso|notevole)\s+(?:che|notare|sottolineare|ricordare|"
    r"osservare|considerare|tenere|precisare|evidenziare|rilevare)\b"
    r"|\b(?:va|vale la pena di|vale la pena)\s+(?:sottolineato|notato|ricordato|detto|osservato|precisato)\b",
    re.I,
)
DOMANDE_MAPPA = {
    "gerundio": "Chi fa l'azione del gerundio? Prova a farne una frase a sé, con il suo soggetto.",
    "nominalizzazioni": "Quali verbi ci sono dentro questi nomi? Prova a dire chi fa che cosa.",
    "connettivo": "Che nesso c'è con la frase prima? Se si capisce già, togli il connettivo.",
    "impersonale": "Importante per chi? Di' direttamente la cosa.",
}


def mappa(testo: str) -> list[dict]:
    """Ogni frase con i costrutti trovati, dalla più carica alla più pulita (a parità, in ordine di testo)."""
    testo = L.normalizza_nfc(testo)
    pos, out = 0, []
    for i, f in enumerate(L.frasi(testo)):
        trovata = testo.find(f[:40], pos)
        if trovata >= 0:
            pos = trovata
        motivi, dettagli = [], []
        ger = [g for g in _RX_GERUNDIO.findall(f) if g.lower() not in _NON_GERUNDI]
        if ger:
            motivi.append("gerundio")
            dettagli.append(", ".join(ger))
        nom = [n for n in _RX_NOMINALIZZAZIONE.findall(f) if n.lower() not in _NON_NOMINALIZZAZIONI]
        if len(nom) >= 2:
            motivi.append("nominalizzazioni")
            dettagli.append(", ".join(nom))
        conn = _RX_CONNETTIVO_APERTURA.match(f.lstrip("«\"“'("))
        if conn:
            motivi.append("connettivo")
            dettagli.append(conn.group(0))
        imp = _RX_IMPERSONALE.search(f)
        if imp:
            motivi.append("impersonale")
            dettagli.append(imp.group(0))
        punti = len(ger) + (len(nom) >= 2) + (len(nom) >= 4) + ("connettivo" in motivi) + ("impersonale" in motivi)
        out.append({"riga": testo.count("\n", 0, pos) + 1, "ordine": i, "frase": f, "punti": punti,
                    "motivi": motivi, "dettagli": dettagli})
    out.sort(key=lambda m: (-m["punti"], m["ordine"]))
    return out


def stampa_mappa(m: list[dict], quota: float = 0.15, out=None) -> None:
    w = lambda s="": print(s, file=out or sys.stdout)  # noqa: E731
    sel = [x for x in m[: max(1, round(len(m) * quota))] if x["punti"] > 0]
    w()
    w(f"MAPPA · le frasi da riscrivere a mano per prime ({len(sel)} su {len(m)}; non entra nel punteggio; non validata, vedi SKILL.md)")
    if not sel:
        w("  Nessuna frase con i quattro costrutti.")
    for x in sel:
        estratto = x["frase"] if len(x["frase"]) <= 110 else x["frase"][:107] + "…"
        w(f"  r{x['riga']:<4} [{x['punti']}] {', '.join(x['motivi'])} · «{estratto}»")
        for motivo, dettaglio in zip(x["motivi"], x["dettagli"]):
            w(f"         {motivo}: {dettaglio} — {DOMANDE_MAPPA[motivo]}")


def _barra(v: float, larghezza: int = 24) -> str:
    pieni = round(v / 100 * larghezza)
    return "#" * pieni + "." * (larghezza - pieni)


def stampa(r: Risultato, titolo: str = "", dettagli: bool = False, out=sys.stdout) -> None:
    w = lambda s="": print(s, file=out)  # noqa: E731
    if titolo:
        w(titolo)
    w(f"{r.parole} parole · {r.frasi} frasi")
    w("=" * 72)
    for c in r.controlli.values():
        nd = "" if c["disponibile"] else " (n/d)"
        w(f"{c['nome']:<12} {_barra(c['punteggio'])} {c['punteggio']:5.1f}   {c['dettaglio']}{nd}")
    w("-" * 72)
    w(f"{'PUNTEGGIO':<12} {_barra(r.punteggio)} {r.punteggio:5.1f}   {r.verdetto}")
    for o in r.ostacoli:
        w(f"  ! {o}")
    if dettagli:
        if r.voci:
            w()
            w("VOCI DEL LESSICO")
            for v in r.voci:
                w(f"  r{v['riga']:<3} [{v['cat']}] «{v['testo']}»" + ("  (debole)" if v["peso"] < 1 else ""))
        if r.tell:
            w()
            w("TELL STRUTTURALI")
            for t in r.tell:
                riga = f"r{t['riga']:<3}" if t["riga"] else "    "
                w(f"  {riga} {t['id']:<20} «{t['estratto']}»")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Punteggio umano di un testo italiano.")
    ap.add_argument("file", nargs="+", help="uno o due file (prima e dopo); - per stdin")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--dettagli", action="store_true", help="elenca voci e tell trovati")
    ap.add_argument("--lessico", help="percorso di un slop.json alternativo")
    ap.add_argument("--taratura", help="file di taratura personale (predefinito: ~/.claude/umanizza/taratura.json se esiste)")
    ap.add_argument("--piattaforma", help="usa le soglie personali di questa piattaforma (threads, linkedin, ...)")
    ap.add_argument("--generico", action="store_true", help="ignora la taratura personale")
    ap.add_argument("--genere", choices=["generico", "accademico"], default="generico",
                    help="accademico: citazioni, rimandi di pagina ed elenchi di fatti non contano")
    ap.add_argument("--mappa", action="store_true", help="elenca le frasi da riscrivere a mano per prime")
    a = ap.parse_args(argv)
    if len(a.file) > 2:
        ap.error("al massimo due file: prima e dopo")
    dati = L.carica(a.lessico)
    soglie = None if a.generico else carica_soglie(a.taratura, a.piattaforma)

    def leggi(f: str) -> str:
        return sys.stdin.read() if f == "-" else Path(f).read_text(encoding="utf-8")

    try:
        testi = [leggi(f) for f in a.file]
    except (OSError, UnicodeDecodeError) as e:
        print(f"detect: non riesco a leggere il file: {e}", file=sys.stderr)
        return 2
    risultati = [analizza(t, dati, soglie, a.genere) for t in testi]
    if soglie and not a.json:
        print(f"Soglie: {soglie['origine']} · PASSA ≥ {soglie['passa']} · SEGNALATO < {soglie['segnalato']}")
    if a.genere == "accademico" and not a.json:
        print("Genere: accademico · citazioni, rimandi di pagina ed elenchi di fatti esclusi · il verdetto qui non distingue "
              "Claude dalle persone (AUC 0,52 su 30+30 testi, 23/11/2026): guarda segnalazioni e fedeltà, non il numero")
    if a.json:
        out = [asdict(r) for r in risultati]
        if a.mappa:
            out[-1]["mappa"] = mappa(testi[-1])
        if len(out) == 2:
            out = {"prima": out[0], "dopo": out[1], "delta": round(out[1]["punteggio"] - out[0]["punteggio"], 1),
                   "fedelta": L.confronta_fatti(testi[0], testi[1])}
        else:
            out = out[0]
        print(json.dumps(out, ensure_ascii=False, indent=2))
    elif len(risultati) == 1:
        stampa(risultati[0], dettagli=a.dettagli)
    else:
        prima, dopo = risultati
        stampa(prima, "PRIMA · " + a.file[0], a.dettagli)
        print()
        stampa(dopo, "DOPO · " + a.file[1], a.dettagli)
        print()
        delta = dopo.punteggio - prima.punteggio
        print(f"DELTA  {delta:+.1f}  ({prima.verdetto} → {dopo.verdetto})")
        for k in PESI:
            d = dopo.controlli[k]["punteggio"] - prima.controlli[k]["punteggio"]
            print(f"  {prima.controlli[k]['nome']:<12} {d:+6.1f}")
        fed = L.confronta_fatti(testi[0], testi[1])
        quota = fed["cambiato"]
        avviso = (" · FERMATI: è cambiato più di metà del testo, controlla che sia ancora di chi lo firma" if quota > 0.5
                  else " · attenzione: è cambiato più del 30%" if quota > 0.3 else "")
        print()
        print(f"FEDELTÀ · parole cambiate {quota:.0%}{avviso}")
        if fed["persi"]:
            print("  spariti (rimettili, se erano fatti): " + ", ".join(fed["persi"][:40]))
        if fed["nuovi"]:
            print("  comparsi (controlla che non siano inventati): " + ", ".join(fed["nuovi"][:40]))
        if not fed["persi"] and not fed["nuovi"]:
            print("  nessun numero, nome o virgolettato perso o aggiunto")
    if a.mappa and not a.json:
        stampa_mappa(mappa(testi[-1]))
    return 1 if risultati[-1].verdetto == "SEGNALATO" else 0


if __name__ == "__main__":
    sys.exit(main())
