"""Detector · prova di conferma (conferma.md): modello salvato, soglia 0,99, testi mai visti."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classifica as K  # noqa: E402

SOGLIA = 0.99


def carica():
    import torch
    from transformers import AutoModelForSequenceClassification, BertTokenizerFast
    b = K.Bert.__new__(K.Bert)
    b.torch = torch
    b.dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
    m = K.D / "modello-addestrato"
    b.tok = BertTokenizerFast.from_pretrained(str(m))
    b.model = AutoModelForSequenceClassification.from_pretrained(str(m), use_safetensors=True).to(b.dev).eval()
    return b


def main() -> int:
    b = carica()
    umani = defaultdict(list)
    for f in sorted((K.D / "web3").rglob("*.txt")):
        umani[f"web3 {f.parent.name}"].append(f)
    umani["ParTUT"] = sorted((K.D / "partut").glob("*.txt"))
    consegne = {json.loads(l)["id"]: json.loads(l)["generatore"] for l in (K.D / "consegne_conferma.jsonl").read_text(encoding="utf-8").splitlines()}
    generati = defaultdict(list)
    for f in sorted((K.D / "gemelli_conferma").glob("*.txt")):
        generati[consegne[f.stem]].append(f)
    generati["gpt quinta lettura (31-40)"] = sorted((K.C / "lettura-cieca-5/gpt_nuovi").glob("*.txt"))
    pu = {k: b.prob([K.leggi(f) for f in v]) for k, v in umani.items()}
    pg = {k: b.prob([K.leggi(f) for f in v]) for k, v in generati.items()}
    tu = [p for v in pu.values() for p in v]
    tg = [p for v in pg.values() for p in v]
    r = {
        "umani": len(tu), "generati": len(tg),
        "auc": round(K.auc([1 - p for p in tu], [1 - p for p in tg]), 4),
        "soglia_099": {"umani_accusati": sum(p >= SOGLIA for p in tu), "quota_umani": round(sum(p >= SOGLIA for p in tu) / len(tu), 4),
                       "generati_riconosciuti": sum(p >= SOGLIA for p in tg), "quota_generati": round(sum(p >= SOGLIA for p in tg) / len(tg), 4)},
        "soglia_05": {"umani_accusati": sum(p >= 0.5 for p in tu), "generati_riconosciuti": sum(p >= 0.5 for p in tg)},
        "per_gruppo_umani": {k: f"{sum(p >= SOGLIA for p in v)}/{len(v)} (a 0,5: {sum(p >= 0.5 for p in v)})" for k, v in pu.items()},
        "per_gruppo_generati": {k: f"{sum(p >= SOGLIA for p in v)}/{len(v)} (a 0,5: {sum(p >= 0.5 for p in v)})" for k, v in pg.items()},
        "accusati": sorted([(round(p, 4), str(f.relative_to(K.D)) if K.D in f.parents else f.name)
                            for k, v in umani.items() for p, f in zip(pu[k], v) if p >= SOGLIA], reverse=True),
        "mancati": sorted([(round(p, 4), f.name) for k, v in generati.items() for p, f in zip(pg[k], v) if p < SOGLIA]),
    }
    c1 = r["soglia_099"]["quota_umani"] <= 0.03
    c2 = r["soglia_099"]["quota_generati"] >= 0.85
    r["criteri"] = {"1_umani_accusati_max_3pc": c1, "2_generati_min_85pc": c2, "esito": "REGGE con soglia 0,99" if c1 and c2 else "NON REGGE"}
    (K.D / "risultati/conferma.json").write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k not in ("accusati", "mancati")}, ensure_ascii=False, indent=1))
    print("accusati:", r["accusati"]); print("mancati:", r["mancati"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
