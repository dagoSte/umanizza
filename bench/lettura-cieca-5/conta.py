"""Lettura 5: conta un braccio. Pari = mezzo. Fedeltà e quota di parole cambiate per testo."""
import difflib, json, re, sys
from pathlib import Path
braccio = sys.argv[1]; L = Path.home() / "umanizza-corpus/lettura-cieca-5" / braccio
sys.path.insert(0, str(Path.home() / "Downloads/umanizza/skills/umanizza"))
import lessico
chiave = {c["coppia"]: c for c in json.loads((L / "chiave.json").read_text(encoding="utf-8"))}
def leggi(nome):
    t = (L / "risposte" / nome).read_text(encoding="utf-8")
    return {r["coppia"]: r for r in json.loads(t[t.index("["): t.rindex("]") + 1])}
def punto(risposta, k):
    if risposta == "pari": return 0.5
    return 1.0 if (risposta == "A") == (chiave[k]["A"] == "riscritto") else 0.0
righe = []
for g, f in (("gpt", "codex.json"), ("claude", "claude.json")):
    r = leggi(f); assert sorted(r) == list(range(1, 21)), (g, sorted(r))
    for k, x in r.items():
        righe.append({"giudice": g, "testo": chiave[k]["testo"], "meglio": punto(x["meglio"], k), "persona": punto(x["persona"], k), "A": x["meglio"] == "A"})
def somma(f, d="meglio"): v = [x[d] for x in righe if f(x)]; return sum(v), len(v)
print(f"BRACCIO {braccio}")
for nome, f in (("tutte le 40 risposte", lambda x: True), ("testi di Claude", lambda x: x["testo"][0] == "c"), ("testi GPT", lambda x: x["testo"][0] == "g"),
                ("giudice Claude", lambda x: x["giudice"] == "claude"), ("giudice GPT", lambda x: x["giudice"] == "gpt")):
    m, n = somma(f); p, _ = somma(f, "persona"); print(f"  {nome:22} meglio {m:4.1f}/{n}   persona {p:4.1f}/{n}")
for g in ("gpt", "claude"): print(f"  giudice {g} sceglie A in {sum(x['A'] for x in righe if x['giudice'] == g)}/20")
fed, identici, fedeli = {}, 0, 0
for n in sorted(p.stem for p in (L / "orig").glob("*.txt")):
    o = (L / "orig" / f"{n}.txt").read_text(encoding="utf-8"); r = (L / "riscritti" / f"{n}.txt").read_text(encoding="utf-8")
    f = lessico.confronta_fatti(o, r); po, pr = re.findall(r"\w+", o.lower()), re.findall(r"\w+", r.lower())
    camb = 1 - sum(b.size for b in difflib.SequenceMatcher(None, po, pr, autojunk=False).get_matching_blocks()) / max(len(po), 1)
    fed[n] = {"persi": f["persi"], "nuovi": f["nuovi"], "cambiate": round(camb, 3)}
    identici += po == pr; fedeli += not f["persi"] and not f["nuovi"]
    if f["persi"] or f["nuovi"]: print("  FEDELTÀ", n, "persi:", f["persi"], "nuovi:", f["nuovi"])
c = sorted(v["cambiate"] for v in fed.values())
print(f"  fedeli {fedeli}/20 · stesse parole dell'originale in {identici}/20 · parole cambiate: mediana {c[10]:.0%}, massimo {c[-1]:.0%}")
json.dump({"righe": righe, "fedelta": fed, "tutte": somma(lambda x: True)[0], "fedeli": fedeli}, open(L / "risultati.json", "w"), ensure_ascii=False, indent=1)
