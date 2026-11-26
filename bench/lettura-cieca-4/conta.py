"""Incrocia le risposte dei giudici con la chiave. Pari = mezzo punto."""
import json, re
from pathlib import Path
L = Path(__file__).resolve().parent
chiave = {c["coppia"]: c for c in json.loads((L / "chiave.json").read_text(encoding="utf-8"))}
def leggi(nome):
    t = (L / "risposte" / nome).read_text(encoding="utf-8")
    return {r["coppia"]: r for r in json.loads(t[t.index("["): t.rindex("]") + 1])}
giudici = {"claude": leggi("claude.json"), "gpt": leggi("gpt.json")}
def punto(risposta, coppia):
    if risposta == "pari": return 0.5
    return 1.0 if (risposta == "A") == (chiave[coppia]["A"] == "riscritto") else 0.0
righe = []
for g, risposte in giudici.items():
    assert sorted(risposte) == list(range(1, 21)), (g, sorted(risposte))
    for k, r in risposte.items():
        testo = chiave[k]["testo"]; autore = "claude" if testo.startswith("c") else "gpt"
        righe.append({"giudice": g, "testo": testo, "incrociato": g != autore,
                      "meglio": punto(r["meglio"], k), "persona": punto(r["persona"], k), "pos_A": r["meglio"] == "A"})
def somma(filtro, dom):
    s = [r[dom] for r in righe if filtro(r)]; return sum(s), len(s)
for nome, f in (("incrociato (principale)", lambda r: r["incrociato"]), ("stesso modello", lambda r: not r["incrociato"]),
                ("tutte", lambda r: True), ("giudice Claude", lambda r: r["giudice"] == "claude"), ("giudice GPT", lambda r: r["giudice"] == "gpt")):
    m, n = somma(f, "meglio"); p, _ = somma(f, "persona")
    print(f"{nome:24} si legge meglio: riscritto {m:4.1f}/{n}   sembra di una persona: riscritto {p:4.1f}/{n}")
for g in giudici:
    a = sum(r["pos_A"] for r in righe if r["giudice"] == g); print(f"giudice {g}: sceglie A in {a}/20 (originale in A in 10/20)")
m, n = somma(lambda r: r["incrociato"], "meglio")
print("ESITO:", "MIGLIORA" if m >= 14 else "NON MIGLIORA" if m < 11 else "INCERTO", f"({m}/{n})")

