#!/usr/bin/env python3
"""umanizza · taratura.py — tara umanizza sui tuoi post, social per social.

La misura generica di umanizza confronta tweet e giornali con post generati:
generi diversi. La taratura confronta te con Claude sugli stessi argomenti,
sulle stesse piattaforme, e salva soglie personali che detect.py usa da lì in poi.

Quattro passi:

  1. importa   legge gli export dei tuoi social e scrive un post per file
     python3 taratura.py importa EXPORT [EXPORT ...] --cartella tara/ [--prima-di 2022-11-30]

     EXPORT può essere:
       - lo zip o la cartella di "Scarica le tue informazioni" di Meta
         (Threads, Instagram, Facebook; formato JSON)
       - Shares.csv dell'export di LinkedIn
       - tweets.js dell'archivio di X/Twitter
       - una cartella di .txt o .md, un post per file (per qualsiasi altro social)

  2. genera    scrive con Claude un post gemello per ogni tuo post: stessa
     piattaforma, stesso argomento, lunghezza simile
     python3 taratura.py genera tara/                 # con ANTHROPIC_API_KEY
     python3 taratura.py genera tara/ --solo-consegne # senza API: Claude li scrive in chat

  3. misura    confronta te e Claude, per piattaforma e a coppie
     python3 taratura.py misura tara/

  4. applica   salva le soglie personali in ~/.claude/umanizza/taratura.json
     python3 taratura.py applica tara/

Niente lascia il tuo computer, tranne le consegne inviate all'API nel passo 2
(se scegli di usarla). Ogni consegna contiene solo le prime 20 parole del tuo
post, per dare l'argomento: il post intero non viene inviato.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import detect  # noqa: E402
import lessico as L  # noqa: E402

TARATURA_PREDEFINITA = Path.home() / ".claude" / "umanizza" / "taratura.json"
MODELLI_PREDEFINITI = ["claude-sonnet-5-5", "claude-haiku-5-5"]
PAROLE_MINIME = 25

# ---------------------------------------------------------------------------
# 1. Importa
# ---------------------------------------------------------------------------


def _ripara_meta(s: str) -> str:
    """Gli export di Meta scrivono l'UTF-8 come latin-1 ("Ã¨" invece di "è")."""
    try:
        return s.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def _data(v) -> datetime | None:
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return datetime.fromtimestamp(v / 1000 if v > 10**11 else v, tz=timezone.utc)
    s = str(v).strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%fZ", "%a %b %d %H:%M:%S %z %Y", "%Y-%m-%d"):
        try:
            d = datetime.strptime(s, fmt)
            return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    if s.isdigit():
        return _data(int(s))
    return None


_CHIAVI_TESTO = ("title", "post", "text", "full_text", "caption", "description")
_CHIAVI_DATA = ("creation_timestamp", "timestamp", "taken_at", "created_at", "date")


def _piattaforma_da_percorso(nome: str) -> str:
    n = nome.lower()
    if "threads" in n or "text_post_app" in n:
        return "threads"
    if "instagram" in n or "/content/posts" in n or "media/posts" in n or "reels" in n:
        return "instagram"
    if "facebook" in n or "your_posts" in n or "your_activity_across_facebook" in n:
        return "facebook"
    return "meta"


def _cammina_json(nodo, piattaforma: str, out: list, data_padre=None):
    """Raccoglie i testi dei post da qualunque JSON di Meta, a prescindere dalla versione."""
    if isinstance(nodo, dict):
        data = next((_data(nodo[k]) for k in _CHIAVI_DATA if k in nodo and not isinstance(nodo[k], (dict, list))), None) or data_padre
        for k in _CHIAVI_TESTO:
            v = nodo.get(k)
            if isinstance(v, str) and v.strip():
                out.append({"piattaforma": piattaforma, "testo": _ripara_meta(v), "data": data})
                break
        for k, v in nodo.items():
            if isinstance(v, (dict, list)):
                _cammina_json(v, piattaforma, out, data)
    elif isinstance(nodo, list):
        for x in nodo:
            _cammina_json(x, piattaforma, out, data_padre)


def _da_meta(nome: str, contenuto: str, out: list):
    nome_l = nome.lower()
    # Commenti, messaggi, like e impostazioni non sono post: si saltano.
    if re.search(r"(?<![a-z])(?:comments?|messages?|inbox|liked|likes?|followers?|following|settings?|logins?|"
                 r"advertisers?|ads|searche?s?|story_interactions)(?![a-z])", nome_l):
        return
    try:
        dati = json.loads(contenuto)
    except json.JSONDecodeError:
        return
    _cammina_json(dati, _piattaforma_da_percorso(nome), out)


def _da_linkedin(contenuto: str, out: list):
    for r in csv.DictReader(io.StringIO(contenuto)):
        testo = r.get("ShareCommentary") or r.get("Commentary") or ""
        if testo.strip():
            out.append({"piattaforma": "linkedin", "testo": testo.replace('""', '"'), "data": _data(r.get("Date"))})


def _da_x(contenuto: str, out: list):
    corpo = contenuto[contenuto.index("[") :] if "[" in contenuto else contenuto
    try:
        dati = json.loads(corpo)
    except json.JSONDecodeError:
        return
    for x in dati:
        t = x.get("tweet", x)
        testo = t.get("full_text") or t.get("text") or ""
        if testo.startswith("RT @"):
            continue  # i retweet non li hai scritti tu
        out.append({"piattaforma": "x", "testo": testo, "data": _data(t.get("created_at"))})


def _leggi_file(nome: str, contenuto: str, out: list, piattaforma_cartella: str | None):
    n = nome.lower()
    if n.endswith("shares.csv"):
        _da_linkedin(contenuto, out)
    elif n.endswith(("tweets.js", "tweet.js")):
        _da_x(contenuto, out)
    elif n.endswith(".json"):
        _da_meta(nome, contenuto, out)
    elif n.endswith((".txt", ".md")):
        out.append({"piattaforma": piattaforma_cartella or "altro", "testo": contenuto, "data": None})


def leggi_export(percorso: Path) -> list[dict]:
    out: list[dict] = []
    if percorso.is_file() and percorso.suffix.lower() == ".zip":
        with zipfile.ZipFile(percorso) as z:
            for nome in z.namelist():
                if nome.lower().endswith((".json", ".csv", ".js")):
                    _leggi_file(nome, z.read(nome).decode("utf-8", errors="replace"), out, None)
    elif percorso.is_file():
        _leggi_file(str(percorso), percorso.read_text(encoding="utf-8", errors="replace"), out, None)
    elif percorso.is_dir():
        for f in sorted(percorso.rglob("*")):
            if f.is_file() and f.suffix.lower() in (".json", ".csv", ".js", ".txt", ".md"):
                if f.suffix.lower() in (".txt", ".md"):
                    piattaforma = f.parent.name.lower() if f.parent != percorso else percorso.name.lower()
                else:
                    piattaforma = None
                _leggi_file(str(f), f.read_text(encoding="utf-8", errors="replace"), out, piattaforma)
    else:
        raise FileNotFoundError(percorso)
    return out


def _pulisci_post(t: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", t.replace("\r\n", "\n")).strip()


def cmd_importa(a) -> int:
    cartella = Path(a.cartella)
    prima_di = _data(a.prima_di) if a.prima_di else None
    tutti, visti = [], set()
    for e in a.export:
        try:
            tutti += leggi_export(Path(e))
        except FileNotFoundError:
            print(f"non trovo {e}", file=sys.stderr)
            return 2
    tenuti, scarti = [], {"corti": 0, "doppi": 0, "dopo la data": 0}
    for p in tutti:
        t = _pulisci_post(p["testo"])
        if len(L.parole(t)) < a.min_parole:
            scarti["corti"] += 1
            continue
        chiave = re.sub(r"\W+", "", t.lower())
        if chiave in visti:
            scarti["doppi"] += 1
            continue
        if prima_di and (p["data"] is None or p["data"] >= prima_di):
            scarti["dopo la data"] += 1
            continue
        visti.add(chiave)
        tenuti.append({**p, "testo": t})
    if not tenuti:
        print("Nessun post tenuto. Controlla il formato dell'export o abbassa --min-parole.", file=sys.stderr)
        return 1
    per_piattaforma: dict[str, int] = {}
    consegne = []
    for p in tenuti:
        pf = p["piattaforma"]
        per_piattaforma[pf] = per_piattaforma.get(pf, 0) + 1
        pid = f"{pf}_{per_piattaforma[pf]:04d}"
        d = cartella / "umano" / pf
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{pid}.txt").write_text(p["testo"] + "\n", encoding="utf-8")
        consegne.append(_consegna(pid, pf, p["testo"]))
    with (cartella / "consegne.jsonl").open("w", encoding="utf-8") as f:
        for c in consegne:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    print(f"Tenuti {len(tenuti)} post: " + ", ".join(f"{k} {v}" for k, v in sorted(per_piattaforma.items())))
    if any(scarti.values()):
        print("Scartati: " + ", ".join(f"{v} {k}" for k, v in scarti.items() if v))
    pochi = [k for k, v in per_piattaforma.items() if v < 30]
    if pochi:
        print(f"Attenzione: sotto i 30 post la misura è fragile ({', '.join(pochi)}).")
    if not prima_di:
        print("Consiglio: se alcuni post li hai scritti con l'IA, rilancia con --prima-di 2022-11-30 "
              "(prima di ChatGPT) o togli a mano quei file da umano/.")
    print(f"Consegne per i gemelli: {cartella / 'consegne.jsonl'}")
    return 0


_NOMI = {"threads": "Threads", "instagram": "una caption Instagram", "facebook": "Facebook", "linkedin": "LinkedIn", "x": "X (Twitter)"}


def _consegna(pid: str, piattaforma: str, testo: str) -> dict:
    parole = L.parole(testo)
    inizio = " ".join(testo.split()[:20])
    dove = _NOMI.get(piattaforma, piattaforma)
    if piattaforma == "accademico":  # genere, non social: il gemello è un brano di tesi
        prompt = (
            f"Scrivi in italiano un brano di una tesi di laurea di circa {len(parole)} parole, in prosa continua. "
            f"L'argomento è quello di un brano che inizia così: «{inizio}…». "
            "Rispondi solo con il testo, senza titolo, introduzioni né note."
        )
    else:
        prompt = (
            f"Scrivi in italiano un post per {dove} di circa {len(parole)} parole. "
            f"L'argomento è quello di un post che inizia così: «{inizio}…». "
            "Rispondi solo con il testo del post, senza introduzioni né note."
        )
    return {"id": pid, "piattaforma": piattaforma, "parole": len(parole), "prompt": prompt}


# ---------------------------------------------------------------------------
# 2. Genera
# ---------------------------------------------------------------------------


def _chiama_api(modello: str, prompt: str, chiave: str) -> str:
    corpo = json.dumps({"model": modello, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=corpo,
        headers={"x-api-key": chiave, "anthropic-version": "2023-06-01", "content-type": "application/json"},
    )
    for tentativo in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                dati = json.loads(r.read())
            return "".join(b.get("text", "") for b in dati.get("content", []) if b.get("type") == "text").strip()
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 529) and tentativo < 3:
                time.sleep(2 ** (tentativo + 2))
                continue
            raise
    return ""


def cmd_genera(a) -> int:
    cartella = Path(a.cartella)
    consegne = [json.loads(r) for r in (cartella / "consegne.jsonl").read_text(encoding="utf-8").splitlines() if r.strip()]
    if a.solo_consegne:
        print(f"{len(consegne)} consegne in {cartella / 'consegne.jsonl'}.")
        print("Per ognuna, scrivi il post e salvalo in ia/<piattaforma>/<id>_claude.txt dentro la cartella.")
        return 0
    chiave = os.environ.get("ANTHROPIC_API_KEY")
    if not chiave:
        print("Manca ANTHROPIC_API_KEY. Esportala, oppure usa --solo-consegne e fai scrivere i gemelli a Claude in chat.",
              file=sys.stderr)
        return 2
    modelli = a.modelli.split(",") if a.modelli else MODELLI_PREDEFINITI
    fatti = saltati = 0
    for c in consegne:
        for m in modelli:
            dest = cartella / "ia" / c["piattaforma"] / f"{c['id']}_{m}.txt"
            if dest.exists():
                saltati += 1
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            try:
                testo = _chiama_api(m, c["prompt"], chiave)
            except urllib.error.HTTPError as e:
                print(f"{c['id']} {m}: errore {e.code}, salto", file=sys.stderr)
                continue
            dest.write_text(testo + "\n", encoding="utf-8")
            fatti += 1
            print(f"\r{fatti} gemelli scritti", end="", file=sys.stderr)
    print(f"\n{fatti} gemelli nuovi, {saltati} già presenti.")
    return 0


# ---------------------------------------------------------------------------
# 3. Misura
# ---------------------------------------------------------------------------


def _auc(pos: list[float], neg: list[float]) -> float:
    if not pos or not neg:
        return float("nan")
    v = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return v / (len(pos) * len(neg))


def _punteggi(cartella: Path, dati: dict, soglie=None) -> dict[str, dict[str, detect.Risultato]]:
    out: dict[str, dict[str, detect.Risultato]] = {}
    for f in sorted(cartella.rglob("*.txt")):
        pf = f.parent.name
        genere = "accademico" if pf == "accademico" else None
        out.setdefault(pf, {})[f.stem] = detect.analizza(f.read_text(encoding="utf-8"), dati, soglie, genere)
    return out


def misura(cartella: Path, dati: dict) -> dict:
    umani = _punteggi(cartella / "umano", dati)
    ia = _punteggi(cartella / "ia", dati) if (cartella / "ia").exists() else {}
    righe = {}
    for pf in sorted(set(umani) | set(ia)):
        u, g = umani.get(pf, {}), ia.get(pf, {})
        su = [r.punteggio for r in u.values()]
        sg = [r.punteggio for r in g.values()]
        # Confronto a coppie: il tuo post contro il suo gemello, stesso argomento.
        vinte = pari = coppie = 0
        for gid, rg in g.items():
            uid = "_".join(gid.split("_")[:2])  # threads_0001_claude-haiku-5-5 → threads_0001
            if uid in u:
                coppie += 1
                if u[uid].punteggio > rg.punteggio:
                    vinte += 1
                elif u[uid].punteggio == rg.punteggio:
                    pari += 1
        controlli = {}
        for k in detect.PESI:
            controlli[k] = round(_auc([r.controlli[k]["punteggio"] for r in u.values()], [r.controlli[k]["punteggio"] for r in g.values()]), 3)
        righe[pf] = {
            "umani": len(su),
            "ia": len(sg),
            "mediana_umani": round(statistics.median(su), 1) if su else None,
            "mediana_ia": round(statistics.median(sg), 1) if sg else None,
            "auc": round(_auc(su, sg), 3),
            "coppie": coppie,
            "vince_umano": round((vinte + 0.5 * pari) / coppie, 3) if coppie else None,
            "controlli": controlli,
            "umani_punteggi": sorted(su),
            "ia_punteggi": sorted(sg),
        }
    return righe


def cmd_misura(a) -> int:
    cartella = Path(a.cartella)
    if not (cartella / "umano").exists():
        print("Prima: taratura.py importa", file=sys.stderr)
        return 2
    r = misura(cartella, L.carica())
    (cartella / "misura.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0
    print(f"{'piattaforma':<12}{'tuoi':>6}{'IA':>6}{'tu':>8}{'IA':>8}{'AUC':>8}{'coppie':>8}{'vinci':>8}")
    print("-" * 64)
    for pf, x in r.items():
        vi = f"{x['vince_umano']:.0%}" if x["vince_umano"] is not None else "-"
        mu = f"{x['mediana_umani']:.1f}" if x["mediana_umani"] is not None else "-"
        mi = f"{x['mediana_ia']:.1f}" if x["mediana_ia"] is not None else "-"
        print(f"{pf:<12}{x['umani']:>6}{x['ia']:>6}{mu:>8}{mi:>8}{x['auc']:>8.3f}{x['coppie']:>8}{vi:>8}")
    print()
    print("AUC: probabilità che un tuo post abbia punteggio più alto di un post di Claude (0.50 = moneta).")
    print("vinci: quante volte il tuo post batte il suo gemello sullo stesso argomento.")
    print()
    print(f"{'AUC per controllo':<16}" + "".join(f"{k[:8]:>10}" for k in detect.PESI))
    for pf, x in r.items():
        print(f"{pf:<16}" + "".join(f"{x['controlli'][k]:>10.3f}" for k in detect.PESI))
    return 0


# ---------------------------------------------------------------------------
# 4. Applica
# ---------------------------------------------------------------------------


def _quantile(xs: list[float], q: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    i = (len(xs) - 1) * q
    lo, hi = int(i), min(int(i) + 1, len(xs) - 1)
    return xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def soglie_personali(umani: list[float], tolleranza: float) -> tuple[float, float]:
    """PASSA: il punteggio sopra cui sta il 90% dei tuoi post. SEGNALATO: sotto il tuo post più basso, meno la tolleranza."""
    passa = round(min(detect.SOGLIA_PASSA, _quantile(umani, 0.10)), 1)
    segnalato = round(min(detect.SOGLIA_SEGNALATO, min(umani) - tolleranza, passa - 5), 1)
    return passa, segnalato


def cmd_applica(a) -> int:
    cartella = Path(a.cartella)
    mpath = cartella / "misura.json"
    if not mpath.exists():
        print("Prima: taratura.py misura", file=sys.stderr)
        return 2
    r = json.loads(mpath.read_text(encoding="utf-8"))
    tutti = [s for x in r.values() for s in x["umani_punteggi"]]
    if len(tutti) < 20:
        print(f"Solo {len(tutti)} tuoi post: troppo pochi per tarare (ne servono almeno 20).", file=sys.stderr)
        return 1
    passa, segn = soglie_personali(tutti, a.tolleranza)
    out = {
        "creata": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "cartella": str(cartella.resolve()),
        "soglia_passa": passa,
        "soglia_segnalato": segn,
        "per_piattaforma": {},
        "nota": "Soglie personali: PASSA = 90% dei tuoi post, SEGNALATO = sotto il tuo post più basso.",
    }
    for pf, x in r.items():
        if len(x["umani_punteggi"]) >= 20:
            p, s = soglie_personali(x["umani_punteggi"], a.tolleranza)
            out["per_piattaforma"][pf] = {"soglia_passa": p, "soglia_segnalato": s, "auc": x["auc"]}
    dest = Path(a.salva) if a.salva else TARATURA_PREDEFINITA
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Soglie personali: PASSA ≥ {passa}, SEGNALATO < {segn}  (generiche: {detect.SOGLIA_PASSA} / {detect.SOGLIA_SEGNALATO})")
    for pf, x in out["per_piattaforma"].items():
        print(f"  {pf:<10} PASSA ≥ {x['soglia_passa']}, SEGNALATO < {x['soglia_segnalato']}")
    ia = [s for x in r.values() for s in x["ia_punteggi"]]
    if ia:
        print(f"Con queste soglie: tuoi post PASSA {sum(s >= passa for s in tutti) / len(tutti):.0%}, "
              f"post di Claude SEGNALATI {sum(s < segn for s in ia) / len(ia):.0%}.")
    print(f"Salvata in {dest}. detect.py la usa da adesso; --generico per ignorarla.")
    print("Nota: le soglie si abbassano, non si alzano mai sopra quelle generiche. "
          "Servono a non segnalare il tuo modo di scrivere, non a essere più severe.")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Tara umanizza sui tuoi post.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("importa", help="legge gli export dei social")
    p.add_argument("export", nargs="+")
    p.add_argument("--cartella", required=True)
    p.add_argument("--prima-di", help="tieni solo i post precedenti a questa data (AAAA-MM-GG)")
    p.add_argument("--min-parole", type=int, default=PAROLE_MINIME)
    p.set_defaults(fn=cmd_importa)
    p = sub.add_parser("genera", help="scrive i gemelli con Claude")
    p.add_argument("cartella")
    p.add_argument("--modelli", help="separati da virgola (predefiniti: " + ",".join(MODELLI_PREDEFINITI) + ")")
    p.add_argument("--solo-consegne", action="store_true")
    p.set_defaults(fn=cmd_genera)
    p = sub.add_parser("misura", help="confronta te e Claude")
    p.add_argument("cartella")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_misura)
    p = sub.add_parser("applica", help="salva le soglie personali")
    p.add_argument("cartella")
    p.add_argument("--tolleranza", type=float, default=3.0)
    p.add_argument("--salva", help=f"dove salvare (predefinito: {TARATURA_PREDEFINITA})")
    p.set_defaults(fn=cmd_applica)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
