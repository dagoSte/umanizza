#!/usr/bin/env python3
"""umanizza · grafici del README, in SVG statico (chiaro e scuro).

Legge i risultati in bench/risultati/ e rifà il confronto prima/dopo su bench/esempi/ con detect.py.
Solo libreria standard: python3 bench/grafici.py [--cartella docs/grafici]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "skills" / "umanizza"))
import detect  # noqa: E402
import lessico as L  # noqa: E402

# Misura del 23/11/2026 sul genere accademico (CHANGELOG 1.2.0): 30 estratti umani contro 30 brani di Claude.
AUC_ACCADEMICO = 0.52

TEMI = {
    "chiaro": {
        "fondo": "#fcfcfb", "testo": "#0b0b0b", "testo2": "#52514e", "tenue": "#898781",
        "griglia": "#e1e0d9", "asse": "#c3c2b7",
        "claude": "#2a78d6", "gpt": "#eb6834", "prima": "#6250d6", "dopo": "#1baf7a",
        "umanizza": "#6250d6", "altro": "#898781",
    },
    "scuro": {
        "fondo": "#1a1a19", "testo": "#f0efec", "testo2": "#c3c2b7", "tenue": "#898781",
        "griglia": "#2c2c2a", "asse": "#383835",
        "claude": "#3987e5", "gpt": "#d95926", "prima": "#9085e9", "dopo": "#199e70",
        "umanizza": "#9085e9", "altro": "#6b6a64",
    },
}
STATO = {"passa": "#0ca30c", "dubbio": "#fab219", "segnalato": "#d03b3b"}
INK_STATO = {"passa": "#ffffff", "dubbio": "#0b0b0b", "segnalato": "#ffffff"}
FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def num(x: float, cifre: int = 2) -> str:
    return f"{x:.{cifre}f}".replace(".", ",")


def barra(x: float, y: float, w: float, h: float, colore: str, r: float = 4) -> str:
    """Barra orizzontale ancorata a sinistra, con l'estremo dei dati arrotondato."""
    if w <= 0:
        return ""
    r = min(r, w, h / 2)
    return (f'<path d="M{x:.1f},{y:.1f} h{w - r:.1f} a{r},{r} 0 0 1 {r},{r} v{h - 2 * r:.1f} '
            f'a{r},{r} 0 0 1 -{r},{r} h-{w - r:.1f} z" fill="{colore}"/>')


def testo(x, y, t, colore, size=13, peso=400, ancora="start") -> str:
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (f'<text x="{x:.1f}" y="{y:.1f}" fill="{colore}" font-size="{size}" font-weight="{peso}" '
            f'text-anchor="{ancora}">{t}</text>')


def svg(larghezza: int, altezza: int, fondo: str, corpo: list[str], titolo: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {larghezza} {altezza}" '
            f'width="{larghezza}" height="{altezza}" font-family="{FONT}" role="img" aria-label="{titolo}">'
            f'<title>{titolo}</title><rect width="100%" height="100%" rx="8" fill="{fondo}"/>'
            + "".join(corpo) + "</svg>\n")


def legenda(x, y, voci, c) -> list[str]:
    out = []
    for etichetta, colore in voci:
        out.append(f'<rect x="{x}" y="{y - 10}" width="12" height="12" rx="3" fill="{colore}"/>')
        out.append(testo(x + 18, y, etichetta, c["testo2"], 12))
        x += 18 + 7.2 * len(etichetta) + 22
    return out


def grafico_auc(righe: list[tuple[str, str, float]], c: dict) -> str:
    """righe: (etichetta, serie 'claude'|'gpt', auc)."""
    W, sx, sw, top, h, passo = 720, 200, 440, 78, 20, 36
    H = top + passo * len(righe) + 46
    k = []
    k.append(testo(24, 32, "Quanto il punteggio separa i testi umani da quelli generati", c["testo"], 15, 600))
    k.append(testo(24, 52, "AUC: 1 = separazione perfetta, 0,5 = caso; web = pagine dello stesso genere", c["testo2"], 12))
    serie = [s for s in ("claude", "gpt") if any(r[1] == s for r in righe)]
    if len(serie) > 1:
        k += legenda(520, 32, [({"claude": "Claude", "gpt": "GPT"}[s], c[s]) for s in serie], c)
    for i, t in enumerate((0, 0.25, 0.5, 0.75, 1)):
        x = sx + sw * t
        k.append(f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{H - 40}" stroke="{c["griglia"]}" stroke-width="1"/>')
        k.append(testo(x, H - 22, num(t, 2 if t not in (0, 1) else 0), c["tenue"], 11, ancora="middle"))
    xc = sx + sw * 0.5
    k.append(f'<line x1="{xc:.1f}" y1="{top - 8}" x2="{xc:.1f}" y2="{H - 40}" stroke="{c["tenue"]}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    k.append(testo(xc + 6, top - 12, "caso", c["tenue"], 11))
    for i, (etichetta, serie, auc) in enumerate(righe):
        y = top + i * passo
        k.append(testo(sx - 12, y + 14.5, etichetta, c["testo"], 13, ancora="end"))
        k.append(barra(sx, y, sw * auc, h, c[serie]))
        k.append(testo(sx + sw * auc + 8, y + 14.5, num(auc), c["testo"], 13, 600))
    k.append(f'<line x1="{sx}" y1="{top - 8}" x2="{sx}" y2="{H - 40}" stroke="{c["asse"]}" stroke-width="1"/>')
    return svg(W, H, c["fondo"], k, "AUC umano contro generato per gruppo")


def grafico_verdetti(righe: list[tuple[str, dict]], c: dict) -> str:
    """righe: (etichetta, {'passa','dubbio','segnalato'} in frazioni)."""
    W, sx, sw, top, h, passo = 720, 200, 480, 92, 24, 40
    H = top + passo * len(righe) + 14
    k = [testo(24, 32, "Verdetti di detect.py per gruppo", c["testo"], 15, 600),
         testo(24, 52, "metà di test del benchmark e testi web anteriori al 2021; GPT, Opus e Fable mai usati per tarare", c["testo2"], 12)]
    k += legenda(sx, 76, [("PASSA ≥ 85", STATO["passa"]), ("DUBBIO 70–85", STATO["dubbio"]),
                          ("SEGNALATO < 70", STATO["segnalato"])], c)
    for i, (etichetta, v) in enumerate(righe):
        y = top + i * passo
        k.append(testo(sx - 12, y + 16.5, etichetta, c["testo"], 13, ancora="end"))
        x = sx
        quote = [(s, v[s]) for s in ("passa", "dubbio", "segnalato") if v[s] > 0]
        for j, (s, q) in enumerate(quote):
            w = sw * q - (2 if j < len(quote) - 1 else 0)
            ultima = j == len(quote) - 1
            if ultima:
                k.append(barra(x, y, w, h, STATO[s]))
            else:
                k.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w, 0):.1f}" height="{h}" fill="{STATO[s]}"/>')
            if w >= 34:
                k.append(testo(x + w / 2, y + 16.5, f"{round(q * 100)}%", INK_STATO[s], 12, 600, "middle"))
            x += sw * q
    return svg(W, H, c["fondo"], k, "Distribuzione dei verdetti per gruppo")


def grafico_prima_dopo(prima: dict, dopo: dict, c: dict) -> str:
    voci = ["ritmo", "concretezza", "slop", "impronta", "voce", "punteggio"]
    W, sx, sw, top, h, passo = 720, 140, 500, 92, 12, 40
    H = top + passo * len(voci) + 10
    k = [testo(24, 32, "Una bozza generata, prima e dopo la revisione", c["testo"], 15, 600),
         testo(24, 52, "bench/esempi/: punteggio per controllo, da 0 a 100", c["testo2"], 12)]
    k += legenda(sx, 76, [("prima", c["prima"]), ("dopo", c["dopo"])], c)
    for i, v in enumerate(voci):
        y = top + i * passo
        peso = 600 if v == "punteggio" else 400
        k.append(testo(sx - 12, y + 18, v.upper(), c["testo"], 12, peso, "end"))
        for j, (serie, d) in enumerate((("prima", prima), ("dopo", dopo))):
            yy = y + j * (h + 2)
            k.append(barra(sx, yy, sw * d[v] / 100, h, c[serie], 3))
            k.append(testo(sx + sw * d[v] / 100 + 6, yy + 10.5, num(d[v], 1), c["testo2"], 11))
    k.append(f'<line x1="{sx}" y1="{top - 6}" x2="{sx}" y2="{H - 14}" stroke="{c["asse"]}" stroke-width="1"/>')
    return svg(W, H, c["fondo"], k, "Punteggi per controllo prima e dopo la revisione")


def grafico_soglie(righe: list[tuple[str, str, int, int, int, int]], c: dict) -> str:
    """righe: (etichetta, serie 'umanizza'|'altro', umani accusati, umani, generati presi, generati). Stessa scala 0-100%."""
    W, sx, pw, gap, top, h, passo = 720, 196, 190, 48, 108, 20, 40
    x1, x2 = sx + 10, sx + 10 + pw + gap
    H = top + passo * len(righe) + 58
    nu, ng = righe[0][3], righe[0][5]
    k = [testo(24, 32, "Chi accusa meno persone, sugli stessi testi nuovi", c["testo"], 15, 600),
         testo(24, 52, f"{nu} testi umani e {ng} generati mai visti · umanizza: verdetto SEGNALATO · classificatore: BERT addestrato da noi",
               c["testo2"], 12)]
    for x0, titolo, nota in ((x1, f"Persone accusate, su {nu}", "meno è meglio"), (x2, f"Testi generati presi, su {ng}", "più è meglio")):
        k.append(testo(x0, 84, titolo, c["testo"], 13, 600))
        k.append(testo(x0, 99, nota, c["tenue"], 11))
        for t in (0, 0.5, 1):
            x = x0 + pw * t
            k.append(f'<line x1="{x:.1f}" y1="{top - 4}" x2="{x:.1f}" y2="{H - 50}" stroke="{c["griglia"]}" stroke-width="1"/>')
            k.append(testo(x, H - 34, f"{round(t * 100)}%", c["tenue"], 11, ancora="middle"))
        k.append(f'<line x1="{x0}" y1="{top - 4}" x2="{x0}" y2="{H - 50}" stroke="{c["asse"]}" stroke-width="1"/>')
    for i, (etichetta, serie, ua, un, gp, gn) in enumerate(righe):
        y = top + i * passo
        peso = 600 if serie == "umanizza" else 400
        k.append(testo(sx - 4, y + 14.5, etichetta, c["testo"], 13, peso, "end"))
        for x0, a, n in ((x1, ua, un), (x2, gp, gn)):
            w = pw * a / n
            k.append(barra(x0, y, w, h, c[serie]))
            q = 100 * a / n
            k.append(testo(x0 + w + 6, y + 14.5, f"{a} · {num(q, 0 if float(q).is_integer() else 1)}%", c["testo2"], 12, 600 if serie == "umanizza" else 400))
    k.append(testo(24, H - 12, "Il prezzo di accusare poche persone: SEGNALATO lascia passare molti testi generati, che finiscono in DUBBIO (da rileggere).",
                   c["testo2"], 11))
    return svg(W, H, c["fondo"], k, "Persone accusate e testi generati presi per soglia, sugli stessi testi nuovi")


def punteggi_esempio(nome: str, dati: dict) -> dict:
    r = detect.analizza((RADICE / "bench" / "esempi" / nome).read_text(encoding="utf-8"), dati)
    d = {k: v["punteggio"] for k, v in r.controlli.items()}
    d["punteggio"] = r.punteggio
    return d


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cartella", default=str(RADICE / "docs" / "grafici"))
    a = ap.parse_args(argv)
    out = Path(a.cartella)
    out.mkdir(parents=True, exist_ok=True)
    ris = RADICE / "bench" / "risultati"
    claude = json.loads((ris / "test.json").read_text(encoding="utf-8"))
    gpt_path = ris / "gpt.json"
    gpt = json.loads(gpt_path.read_text(encoding="utf-8")) if gpt_path.exists() else None

    righe_auc = [("Sonnet e Haiku · tweet", "claude", claude["auc"]["social"]["auc_totale"]),
                 ("Sonnet e Haiku · prosa", "claude", claude["auc"]["prosa"]["auc_totale"])]
    if gpt:
        righe_auc += [("GPT · tweet", "gpt", gpt["auc"]["social"]["auc_totale"]),
                      ("GPT · prosa", "gpt", gpt["auc"]["prosa"]["auc_totale"])]
    web_c, web_g = (ris / "web_claude.json"), (ris / "web_gpt.json")
    if web_c.exists() and web_g.exists():
        righe_auc += [("Sonnet e Haiku · web", "claude", json.loads(web_c.read_text(encoding="utf-8"))["auc"]["tutti"]["auc_totale"]),
                      ("GPT · web", "gpt", json.loads(web_g.read_text(encoding="utf-8"))["auc"]["tutti"]["auc_totale"])]
    for nome, f in (("Opus · prosa", "opus.json"), ("Fable · prosa", "fable.json")):
        if (ris / f).exists():
            righe_auc.append((nome, "claude", json.loads((ris / f).read_text(encoding="utf-8"))["auc"]["prosa"]["auc_totale"]))
    righe_auc.append(("Sonnet e Haiku · tesi", "claude", AUC_ACCADEMICO))

    gruppi = {g["nome"]: g for g in claude["gruppi"]}
    righe_v = [(f"Persone · tweet ({gruppi['umano (social)']['n']})", gruppi["umano (social)"]),
               (f"Persone · prosa ({gruppi['umano (prosa)']['n']})", gruppi["umano (prosa)"])]
    if web_g.exists():
        w = next(x for x in json.loads(web_g.read_text(encoding="utf-8"))["gruppi"] if x["nome"].startswith("umano"))
        righe_v.append((f"Persone · web ({w['n']})", w))
    righe_v += [
               (f"Sonnet e Haiku ({gruppi['IA (test)']['n']})", gruppi["IA (test)"])]
    if gpt:
        g = next(x for x in gpt["gruppi"] if x["nome"].startswith("IA"))
        righe_v.append((f"GPT ({g['n']})", g))
    for nome, f in (("Opus", "opus.json"), ("Fable", "fable.json")):
        if (ris / f).exists():
            g = next(x for x in json.loads((ris / f).read_text(encoding="utf-8"))["gruppi"] if x["nome"].startswith("IA"))
            righe_v.append((f"{nome} ({g['n']})", g))

    righe_s = None
    cl = RADICE / "bench" / "classificatore" / "risultati"
    if (cl / "conferma.json").exists() and (cl / "confronto_detect.json").exists():
        conf = json.loads((cl / "conferma.json").read_text(encoding="utf-8"))
        det = json.loads((cl / "confronto_detect.json").read_text(encoding="utf-8"))
        nu, ng = conf["umani"], conf["generati"]
        seg = det["conferma_umani_web3"].get("SEGNALATO", 0) + det["conferma_umani_partut"].get("SEGNALATO", 0)
        assert det["conferma_umani_web3"]["n"] + det["conferma_umani_partut"]["n"] == nu and det["conferma_generati"]["n"] == ng
        righe_s = [("umanizza · SEGNALATO", "umanizza", seg, nu, det["conferma_generati"].get("SEGNALATO", 0), ng),
                   ("Classificatore · soglia 0,99", "altro", conf["soglia_099"]["umani_accusati"], nu, conf["soglia_099"]["generati_riconosciuti"], ng),
                   ("Classificatore · soglia 0,5", "altro", conf["soglia_05"]["umani_accusati"], nu, conf["soglia_05"]["generati_riconosciuti"], ng)]

    dati = L.carica()
    prima, dopo = punteggi_esempio("peggiore.txt", dati), punteggi_esempio("riscritto.txt", dati)
    for tema, c in TEMI.items():
        (out / f"auc-{tema}.svg").write_text(grafico_auc(righe_auc, c), encoding="utf-8")
        (out / f"verdetti-{tema}.svg").write_text(grafico_verdetti(righe_v, c), encoding="utf-8")
        (out / f"prima-dopo-{tema}.svg").write_text(grafico_prima_dopo(prima, dopo, c), encoding="utf-8")
        if righe_s:
            (out / f"soglie-{tema}.svg").write_text(grafico_soglie(righe_s, c), encoding="utf-8")
    print(f"Grafici in {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
