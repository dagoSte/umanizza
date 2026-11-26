"""Braccio 4b: incrocia le risposte con la chiave (pari = mezzo), fedeltà e quota di parole cambiate."""
import difflib, json, re, sys
from pathlib import Path
L = Path.home() / "umanizza-corpus/lettura-cieca-4b"
sys.path.insert(0, str(Path.home() / "Downloads/umanizza/skills/umanizza"))
import lessico
chiave = {c["coppia"]: c for c in json.loads((L / "chiave.json").read_text(encoding="utf-8"))}
def leggi(nome):
    t = (L / "risposte" / nome).read_text(encoding="utf-8")
    return {r["coppia"]: r for r in json.loads(t[t.index("["): t.rindex("]") + 1])}
def punto(risposta, k):
    if risposta == "pari": return 0.5
    return 1.0 if (risposta == "A") == (chiave[k]["A"] == "riscritto") else 0.0
out = {}
for g, f in (("gpt", "codex.json"), ("claude", "claude.json")):
    r = leggi(f); assert sorted(r) == list(range(1, 11)), (g, sorted(r))
    m = sum(punto(x["meglio"], k) for k, x in r.items()); p = sum(punto(x["persona"], k) for k, x in r.items())
    a = sum(x["meglio"] == "A" for x in r.values())
    out[g] = {"meglio": m, "persona": p, "sceglie_A": a, "per_testo": {chiave[k]["testo"]: punto(x["meglio"], k) for k, x in sorted(r.items())}}
    print(f"giudice {g:6} si legge meglio: riscritto {m:4.1f}/10   sembra di una persona: {p:4.1f}/10   sceglie A in {a}/10")
fed = {}
for n in sorted(p.stem for p in (L / "orig").glob("x*.txt")):
    o = (L / "orig" / f"{n}.txt").read_text(encoding="utf-8"); r = (L / "riscritti" / f"{n}.txt").read_text(encoding="utf-8")
    f = lessico.confronta_fatti(o, r); po, pr = re.findall(r"\w+", o.lower()), re.findall(r"\w+", r.lower())
    camb = 1 - sum(b.size for b in difflib.SequenceMatcher(None, po, pr, autojunk=False).get_matching_blocks()) / max(len(po), 1)
    fed[n] = {"persi": f["persi"], "nuovi": f["nuovi"], "cambiate": round(camb, 2)}
    print(n, f"parole cambiate {camb:.0%}", "persi:", f["persi"], "nuovi:", f["nuovi"])
m = out["gpt"]["meglio"]
print("ESITO (giudice GPT):", "REGGE" if m >= 7 else "NO" if m < 5 else "INCERTO", f"({m}/10)")
json.dump({"giudici": out, "fedelta": fed}, open(L / "risultati.json", "w"), ensure_ascii=False, indent=1)
