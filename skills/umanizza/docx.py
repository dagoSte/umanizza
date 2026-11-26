#!/usr/bin/env python3
"""umanizza · docx.py — file Word: estrae il testo e applica modifiche come revisioni tracciate, con verifiche.

Uso:
  python3 docx.py estrai capitolo.docx [--note] [-o testo.txt]
  python3 docx.py applica capitolo.docx modifiche.json -o revisioni.docx [--accettate] [--autore NOME]

modifiche.json è una lista di {"id": "...", "vecchio": "...", "nuovo": "..."}:
  "nuovo": null   toglie il paragrafo intero, che deve contenere esattamente "vecchio";
  "parte": "note" lavora sulle note a piè di pagina invece che sul corpo.
Il confronto ignora ' contro ’ e lo spazio indivisibile, e non attraversa mai richiami di nota, tabulazioni
o campi. Le modifiche le decide chi rivede (vedi «File Word» in SKILL.md): lo script le applica e controlla.

Dopo «applica» controlla da solo: XML valido; rifiutando tutte le revisioni si torna al testo originale;
richiami di nota rimasti sulla loro frase; numeri, nomi e virgolettati persi o comparsi.
Esce con 1 se una modifica non si applica o una verifica bloccante fallisce, 2 se non legge i file.
Solo libreria standard, nessuna rete.
"""
from __future__ import annotations

import argparse
import difflib
import html
import json
import re
import sys
import xml.dom.minidom
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lessico as L  # noqa: E402

PARTI = {"corpo": "word/document.xml", "note": "word/footnotes.xml"}
_RX_PAR = re.compile(r"<w:p[ >].*?</w:p>", re.S)
_RX_RUN = re.compile(r"<w:r(?: [^>]*)?>(.*?)</w:r>", re.S)
_RX_T = re.compile(r"<w:t(?: [^>]*)?>([^<]*)</w:t>")


def _norm(s: str) -> str:
    return s.replace("’", "'").replace(" ", " ")


def _tok(s: str) -> list[str]:
    return re.findall(r"\s+|\w+|[^\w\s]", s)


# --------------------------------------------------------------------------
# Lettura
# --------------------------------------------------------------------------


def _vista(xml_parte: str, modo: str) -> str:
    """Il XML come apparirebbe accettando ("accetta") o rifiutando ("rifiuta") tutte le revisioni."""
    if modo == "accetta":
        xml_parte = re.sub(r"<w:del [^>]*/>", "", xml_parte)
        return re.sub(r"<w:del [^>]*>.*?</w:del>", "", xml_parte, flags=re.S)
    xml_parte = re.sub(r"<w:ins [^>]*>.*?</w:ins>", "", xml_parte, flags=re.S)
    return xml_parte.replace("<w:delText", "<w:t").replace("</w:delText>", "</w:t>")


def _paragrafi(xml_parte: str) -> list[str]:
    out = []
    for p in _RX_PAR.findall(xml_parte):
        t = html.unescape("".join(_RX_T.findall(p))).strip()
        if t:
            out.append(t)
    return out


def _leggi(path: Path) -> dict[str, str]:
    with zipfile.ZipFile(path) as z:
        nomi = set(z.namelist())
        return {k: z.read(v).decode("utf-8") for k, v in PARTI.items() if v in nomi}


def estrai(path, note: bool = False, modo: str = "accetta") -> str:
    """Testo del corpo, un paragrafo per riga; con note=True le note in fondo, dopo una riga NOTE."""
    parti = _leggi(Path(path))
    righe = _paragrafi(_vista(parti["corpo"], modo))
    if note and "note" in parti:
        righe += ["", "NOTE"] + _paragrafi(_vista(parti["note"], modo))
    return "\n".join(righe)


# --------------------------------------------------------------------------
# Scrittura: revisioni tracciate
# --------------------------------------------------------------------------


class _Revisore:
    def __init__(self, autore: str, accettate: bool):
        self.autore, self.accettate, self.id = autore, accettate, 9000
        self.data = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def _rev(self, tipo: str, dentro: str) -> str:
        self.id += 1
        return f'<w:{tipo} w:id="{self.id}" w:author="{html.escape(self.autore)}" w:date="{self.data}">{dentro}</w:{tipo}>'

    @staticmethod
    def _pezzi(p: str) -> list[tuple]:
        """('xml', testo) per ciò che non si tocca, ('run', rPr, testo) per i run di solo testo."""
        pezzi, pos = [], 0
        for m in _RX_RUN.finditer(p):
            if m.start() > pos:
                pezzi.append(("xml", p[pos:m.start()]))
            testa = re.match(r"\s*(<w:rPr>.*?</w:rPr>)?", m.group(1), re.S)
            resto = m.group(1)[len(testa.group(0)):]
            if re.fullmatch(r"(?:<w:t(?: [^>]*)?>[^<]*</w:t>|<w:t/>)*", resto.strip()):
                pezzi.append(("run", testa.group(1) or "", html.unescape("".join(_RX_T.findall(resto)))))
            else:
                pezzi.append(("xml", m.group(0)))  # richiamo di nota, tabulazione, campo: opaco
            pos = m.end()
        pezzi.append(("xml", p[pos:]))
        return pezzi

    @staticmethod
    def _runs(chars: list[tuple[str, str]], tag: str = "t") -> str:
        out, i = [], 0
        while i < len(chars):
            j = i
            while j < len(chars) and chars[j][1] == chars[i][1]:
                j += 1
            testo = html.escape("".join(c for c, _ in chars[i:j]), quote=False)
            out.append(f'<w:r>{chars[i][1]}<w:{tag} xml:space="preserve">{testo}</w:{tag}></w:r>')
            i = j
        return "".join(out)

    def sostituisci(self, p: str, vecchio: str, nuovo: str) -> str | None:
        pezzi = self._pezzi(p)
        chars, owner = [], []
        for k, pz in enumerate(pezzi):
            for c in (pz[2] if pz[0] == "run" else "\x00"):
                chars.append((c, pz[1] if pz[0] == "run" else None))
                owner.append(k)
        testo, v = _norm("".join(c for c, _ in chars)), _norm(vecchio)
        if not v or testo.count(v) != 1:
            return None
        a, b = testo.index(v), testo.index(v) + len(v)
        k0, k1 = owner[a], owner[b - 1]
        s = owner.index(k0)
        e = len(owner) - owner[::-1].index(k1)
        tratto = chars[a:b]
        nuovo = nuovo.replace("'", "’")
        vt, nt = _tok("".join(c for c, _ in tratto)), _tok(nuovo)
        sm = difflib.SequenceMatcher(None, [_norm(x) for x in vt], [_norm(x) for x in nt], autojunk=False)
        xml_out, pos = [], 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            lv = sum(len(x) for x in vt[i1:i2])
            seg = tratto[pos:pos + lv]
            if seg:
                rpr = seg[0][1]
            else:  # inserimento puro: preferisci il vicino senza formattazione
                vicini = [x for x in (tratto[pos - 1][1] if pos else None, tratto[pos][1] if pos < len(tratto) else None) if x is not None]
                rpr = "" if "" in vicini else vicini[0]
            if op == "equal":
                xml_out.append(self._runs(seg))
            else:
                if lv and not self.accettate:
                    xml_out.append(self._rev("del", self._runs(seg, "delText")))
                if j2 > j1:
                    ins = self._runs([(c, rpr) for c in "".join(nt[j1:j2])])
                    xml_out.append(ins if self.accettate else self._rev("ins", ins))
            pos += lv
        ricostruisci = lambda pz: pz[1] if pz[0] == "xml" else f'<w:r>{pz[1]}<w:t xml:space="preserve">{html.escape(pz[2], quote=False)}</w:t></w:r>'  # noqa: E731
        return ("".join(map(ricostruisci, pezzi[:k0])) + self._runs(chars[s:a]) + "".join(xml_out)
                + self._runs(chars[b:e]) + "".join(map(ricostruisci, pezzi[k1 + 1:])))

    def togli_paragrafo(self, p: str, vecchio: str) -> str | None:
        testo = "".join(pz[2] for pz in self._pezzi(p) if pz[0] == "run")
        if _norm(testo).strip() != _norm(vecchio).strip() or "<w:footnoteReference" in p:
            return None
        if self.accettate:
            return ""
        corpo = _RX_RUN.sub(lambda m: self._rev("del", m.group(0).replace("<w:t", "<w:delText").replace("</w:t>", "</w:delText>")), p)
        self.id += 1
        segno = f'<w:del w:id="{self.id}" w:author="{html.escape(self.autore)}" w:date="{self.data}"/>'
        ppr = re.search(r"<w:pPr>.*?</w:pPr>", corpo, re.S)
        if ppr:
            nuovo_ppr = (ppr.group(0).replace("<w:rPr>", "<w:rPr>" + segno, 1) if "<w:rPr>" in ppr.group(0)
                         else ppr.group(0).replace("</w:pPr>", f"<w:rPr>{segno}</w:rPr></w:pPr>"))
            return corpo.replace(ppr.group(0), nuovo_ppr, 1)
        return re.sub(r"^(<w:p(?: [^>]*)?>)", lambda m: m.group(1) + f"<w:pPr><w:rPr>{segno}</w:rPr></w:pPr>", corpo)


# --------------------------------------------------------------------------
# Verifiche
# --------------------------------------------------------------------------


def _frase_prima_delle_note(xml_parte: str) -> dict[str, str]:
    """Per ogni nota, numerata come la vede chi legge (1, 2, 3…), l'ultima frase che la precede nel paragrafo."""
    out = {}
    for p in _RX_PAR.findall(xml_parte):
        testo = ""
        for m in re.finditer(r'<w:t(?: [^>]*)?>([^<]*)</w:t>|<w:footnoteReference w:id="(\d+)"', p):
            if m.group(2):
                out[str(len(out) + 1)] = re.split(r"(?<=[.!?])\s+", testo.strip())[-1] if testo.strip() else ""
            else:
                testo += html.unescape(m.group(1))
    return out


def verifica(originale: Path, uscita: Path, accettate: bool) -> dict:
    prima, dopo = _leggi(originale), _leggi(uscita)
    esito = {"xml": True}
    try:
        for t in dopo.values():
            xml.dom.minidom.parseString(t.encode("utf-8"))
    except Exception:  # XML rotto: Word non apre il file
        esito["xml"] = False
    esito["rifiuta_uguale_originale"] = None if accettate else (
        estrai(uscita, note=True, modo="rifiuta") == estrai(originale, note=True))
    a, b = _frase_prima_delle_note(prima["corpo"]), _frase_prima_delle_note(_vista(dopo["corpo"], "accetta"))
    esito["note_spostate"] = [
        {"nota": k, "prima": a[k], "dopo": b.get(k, "")} for k in a
        if difflib.SequenceMatcher(None, L.parole(a[k]), L.parole(b.get(k, "")), autojunk=False).ratio() < 0.5
    ]
    esito["fedelta"] = L.confronta_fatti(estrai(originale, note=True), estrai(uscita, note=True))
    return esito


# --------------------------------------------------------------------------
# Applica
# --------------------------------------------------------------------------


def applica(originale, modifiche: list[dict], uscita, accettate: bool = False, autore: str = "umanizza") -> dict:
    originale, uscita = Path(originale), Path(uscita)
    rev = _Revisore(autore, accettate)
    with zipfile.ZipFile(originale) as zin:
        parti = {k: zin.read(v).decode("utf-8") for k, v in PARTI.items() if v in zin.namelist()}
        esiti = []
        for m in modifiche:
            doc = parti.get(m.get("parte", "corpo"), "")
            chiave = _norm(m["vecchio"])[:25]
            fatto = False
            for pm in _RX_PAR.finditer(doc):
                if chiave not in _norm(html.unescape(re.sub(r"<[^>]+>", "", pm.group(0)))):
                    continue
                nuovo_p = (rev.togli_paragrafo(pm.group(0), m["vecchio"]) if m["nuovo"] is None
                           else rev.sostituisci(pm.group(0), m["vecchio"], m["nuovo"]))
                if nuovo_p is not None:
                    parti[m.get("parte", "corpo")] = doc[:pm.start()] + nuovo_p + doc[pm.end():]
                    fatto = True
                    break
            esiti.append({"id": m.get("id", ""), "esito": "ok" if fatto else "NON APPLICATA"})
        inverso = {v: k for k, v in PARTI.items()}
        with zipfile.ZipFile(uscita, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                k = inverso.get(item.filename)
                zout.writestr(item, parti[k].encode("utf-8") if k in parti else zin.read(item.filename))
    return {"modifiche": esiti, "verifiche": verifica(originale, uscita, accettate)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="File Word: estrai il testo o applica modifiche come revisioni tracciate.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("estrai", help="testo del corpo (e delle note)")
    e.add_argument("file")
    e.add_argument("--note", action="store_true", help="aggiunge le note a piè di pagina in fondo")
    e.add_argument("-o", "--out")
    p = sub.add_parser("applica", help="modifiche come revisioni tracciate, con verifiche")
    p.add_argument("file")
    p.add_argument("modifiche")
    p.add_argument("-o", "--out", required=True)
    p.add_argument("--accettate", action="store_true", help="scrive le modifiche già accettate, senza revisioni")
    p.add_argument("--autore", default="umanizza", help="nome dell'autore delle revisioni in Word")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "estrai":
            t = estrai(a.file, a.note)
            if a.out:
                Path(a.out).write_text(t + "\n", encoding="utf-8")
            else:
                print(t)
            return 0
        mods = json.loads(Path(a.modifiche).read_text(encoding="utf-8"))
        r = applica(a.file, mods, a.out, a.accettate, a.autore)
    except (OSError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as err:
        print(f"docx: non riesco a leggere i file: {err}", file=sys.stderr)
        return 2
    for m in r["modifiche"]:
        print(f"  {m['id']:<40} {m['esito']}")
    v = r["verifiche"]
    print("VERIFICHE")
    print(f"  XML valido: {'sì' if v['xml'] else 'NO'}")
    if v["rifiuta_uguale_originale"] is not None:
        print(f"  rifiutando tutto si torna all'originale: {'sì' if v['rifiuta_uguale_originale'] else 'NO'}")
    if v["note_spostate"]:
        for n in v["note_spostate"]:
            print(f"  ! nota {n['nota']}: la frase che la precede è cambiata, controlla che sia ancora quella giusta: "
                  f"«…{n['prima'][-60:]}» → «…{n['dopo'][-60:]}»")
    else:
        print("  richiami di nota: tutti sulla loro frase")
    f = v["fedelta"]
    print(f"  fedeltà: parole cambiate {f['cambiato']:.0%}"
          + (f" · spariti: {', '.join(f['persi'][:20])}" if f["persi"] else "")
          + (f" · comparsi: {', '.join(f['nuovi'][:20])}" if f["nuovi"] else ""))
    bloccante = (any(m["esito"] != "ok" for m in r["modifiche"]) or not v["xml"]
                 or v["rifiuta_uguale_originale"] is False)
    return 1 if bloccante else 0


if __name__ == "__main__":
    sys.exit(main())
