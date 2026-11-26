"""Detector · addestra il classificatore pre-registrato e lo verifica sui testi dell'indice.

    python3.13 -I script/classifica.py            # addestra, verifica, scrive risultati/esito.json
    python3.13 -I script/classifica.py --solo-base # solo il confronto di base (TF-IDF)

Tutto quello che si sceglie è fissato in preregistrazione.md: qui non si mette a punto nulla sui dati di verifica.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path

CASA = Path.home()
D = CASA / "umanizza-corpus/detector"
REPO = CASA / "Downloads/umanizza"
C = CASA / "umanizza-corpus"
sys.path.insert(0, str(REPO / "skills/umanizza"))
import detect  # noqa: E402
import lessico as L  # noqa: E402

SEME = 20261127
FINESTRA, MAX_FINESTRE = 256, 3
EPOCHE, LR, BATCH, WD, WARMUP = 3, 2e-5, 8, 0.01, 0.10


# ---------------------------------------------------------------------------
# Normalizzazione uguale per tutti
# ---------------------------------------------------------------------------
def normalizza(t: str) -> str:
    t = re.sub(r"```.*?```", " ", t, flags=re.S)
    t = re.sub(r"^\s{0,3}#{1,6}\s*", "", t, flags=re.M)          # titoli markdown
    t = re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", t, flags=re.M)   # punti d'elenco a inizio riga
    t = t.replace("**", "").replace("__", "").replace("`", "")
    t = re.sub(r"(?<!\w)\*(?!\s)([^*\n]+?)(?<!\s)\*(?!\w)", r"\1", t)  # corsivo *x*
    t = t.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", t).strip()


def leggi(p: Path) -> str:
    return p.read_text(encoding="utf-8").strip()


def txt(cartella: Path) -> list[Path]:
    return sorted(cartella.rglob("*.txt"))


# ---------------------------------------------------------------------------
# Dati
# ---------------------------------------------------------------------------
def dati_addestramento():
    coppie = []
    for riga in (D / "consegne.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(riga)
        g = D / "gemelli" / f"{r['id']}.txt"
        if g.exists() and g.stat().st_size:
            coppie.append((r["id"], leggi(Path(r["umano"])), leggi(g), r["genere"], r["generatore"]))
    rnd = random.Random(SEME)
    ids = sorted(c[0] for c in coppie)
    rnd.shuffle(ids)
    val = set(ids[: round(len(ids) * 0.15)])
    tr = [c for c in coppie if c[0] not in val]
    va = [c for c in coppie if c[0] in val]
    return coppie, tr, va


def dati_verifica():
    B = REPO / "bench"
    umani = {"prosa": txt(B / "corpus_umano/test/prosa"), "social": txt(B / "corpus_umano/test/social"), "web2": txt(D / "web2")}
    generati = {"sonnet_haiku": txt(B / "corpus_ia/test"), "gpt": txt(B / "corpus_gpt"),
                "opus": txt(B / "corpus_claude_forti/opus"), "fable": txt(B / "corpus_claude_forti/fable")}
    return umani, generati


def auc(pos: list[float], neg: list[float]) -> float:
    v = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return v / (len(pos) * len(neg))


# ---------------------------------------------------------------------------
# Modello
# ---------------------------------------------------------------------------
class Bert:
    def __init__(self):
        import torch
        from transformers import AutoModelForSequenceClassification, BertTokenizerFast
        self.torch = torch
        torch.manual_seed(SEME)
        random.seed(SEME)
        self.dev = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
        m = D / "modello-bert"
        self.tok = BertTokenizerFast(vocab_file=str(m / "vocab.txt"), do_lower_case=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(str(m), num_labels=2, use_safetensors=True).to(self.dev)

    def finestre(self, testo: str) -> list[list[int]]:
        ids = self.tok(normalizza(testo), add_special_tokens=False)["input_ids"]
        n = FINESTRA - 2
        pezzi = [ids[i:i + n] for i in range(0, max(len(ids), 1), n)][:MAX_FINESTRE]
        return [[self.tok.cls_token_id] + p + [self.tok.sep_token_id] for p in pezzi if p]

    def _batch(self, seq: list[list[int]]):
        t = self.torch
        lung = max(len(s) for s in seq)
        ids = t.tensor([s + [0] * (lung - len(s)) for s in seq], device=self.dev)
        att = t.tensor([[1] * len(s) + [0] * (lung - len(s)) for s in seq], device=self.dev)
        return ids, att

    def addestra(self, esempi: list[tuple[str, int]]):
        t = self.torch
        from transformers import get_linear_schedule_with_warmup
        fin = [(f, y) for testo, y in esempi for f in self.finestre(testo)]
        passi = EPOCHE * ((len(fin) + BATCH - 1) // BATCH)
        opt = t.optim.AdamW(self.model.parameters(), lr=LR, weight_decay=WD)
        sch = get_linear_schedule_with_warmup(opt, int(WARMUP * passi), passi)
        rnd = random.Random(SEME)
        self.model.train()
        t0 = time.time()
        for ep in range(EPOCHE):
            rnd.shuffle(fin)
            perdita = []
            for i in range(0, len(fin), BATCH):
                b = fin[i:i + BATCH]
                ids, att = self._batch([f for f, _ in b])
                y = t.tensor([y for _, y in b], device=self.dev)
                out = self.model(input_ids=ids, attention_mask=att, labels=y)
                out.loss.backward()
                t.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step(); sch.step(); opt.zero_grad()
                perdita.append(out.loss.item())
            print(f"  epoca {ep + 1}: perdita media {statistics.fmean(perdita):.4f} · {len(fin)} finestre · {time.time() - t0:.0f} s", flush=True)
        self.model.eval()

    def prob(self, testi: list[str]) -> list[float]:
        """Probabilità che il testo sia generato: media delle sue finestre."""
        t = self.torch
        out = []
        with t.no_grad():
            for testo in testi:
                fin = self.finestre(testo)
                ids, att = self._batch(fin)
                p = t.softmax(self.model(input_ids=ids, attention_mask=att).logits, dim=-1)[:, 1]
                out.append(float(p.mean()))
        return out


class Base:
    """Confronto di base: TF-IDF su n-grammi di caratteri 2-5 e regressione logistica."""
    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        self.v = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), min_df=2, sublinear_tf=True)
        self.m = LogisticRegression(max_iter=2000, random_state=SEME)

    def addestra(self, esempi):
        X = self.v.fit_transform([normalizza(t) for t, _ in esempi])
        self.m.fit(X, [y for _, y in esempi])

    def prob(self, testi):
        return [float(p) for p in self.m.predict_proba(self.v.transform([normalizza(t) for t in testi]))[:, 1]]


# ---------------------------------------------------------------------------
# Verifica
# ---------------------------------------------------------------------------
def verifica(nome: str, clf, val, umani, generati) -> dict:
    r: dict = {"nome": nome}
    pu = clf.prob([u for _, u, _, _, _ in val]); pg = clf.prob([g for _, _, g, _, _ in val])
    r["validazione"] = {"auc": round(auc([1 - p for p in pu], [1 - p for p in pg]), 4),
                        "umani_sopra_05": sum(p >= 0.5 for p in pu), "gemelli_sotto_05": sum(p < 0.5 for p in pg), "coppie": len(val)}
    pu_t = {k: clf.prob([leggi(f) for f in v]) for k, v in umani.items()}
    pg_t = {k: clf.prob([leggi(f) for f in v]) for k, v in generati.items()}
    conf = {}
    for u in ("prosa", "social", "web2"):
        for g in generati:
            conf[f"{u}~{g}"] = round(auc([1 - p for p in pu_t[u]], [1 - p for p in pg_t[g]]), 4)
    r["confronti"] = conf
    r["auc_media"] = round(statistics.fmean(conf.values()), 4)
    r["auc_minima"] = min(conf.values())
    tutti_u = [p for v in pu_t.values() for p in v]; tutti_g = [p for v in pg_t.values() for p in v]
    r["umani_giudicati_generati"] = {"n": sum(p >= 0.5 for p in tutti_u), "su": len(tutti_u), "quota": round(sum(p >= 0.5 for p in tutti_u) / len(tutti_u), 4),
                                     "per_gruppo": {k: sum(p >= 0.5 for p in v) for k, v in pu_t.items()}}
    r["generati_riconosciuti"] = {"n": sum(p >= 0.5 for p in tutti_g), "su": len(tutti_g),
                                  "per_gruppo": {k: f"{sum(p >= 0.5 for p in v)}/{len(v)}" for k, v in pg_t.items()}}
    r["_prob"] = {"umani": {k: v for k, v in pu_t.items()}, "generati": {k: v for k, v in pg_t.items()}}
    return r


def detect_riferimento(umani, generati) -> dict:
    dati = L.carica()
    s = lambda f: detect.analizza(leggi(f), dati).punteggio  # noqa: E731
    su = {k: [s(f) for f in v] for k, v in umani.items()}
    sg = {k: [s(f) for f in v] for k, v in generati.items()}
    conf = {f"{u}~{g}": round(auc(su[u], sg[g]), 4) for u in ("prosa", "social", "web2") for g in generati}
    return {"confronti": conf, "auc_media": round(statistics.fmean(conf.values()), 4), "_punteggi": {"umani": su, "generati": sg}}


def combinazione(rif, ris) -> dict:
    """Media dei ranghi di detect.py e del classificatore, per confronto."""
    conf = {}
    for chiave in ris["confronti"]:
        u, g = chiave.split("~")
        a = rif["_punteggi"]["umani"][u] + rif["_punteggi"]["generati"][g]
        b = [1 - p for p in ris["_prob"]["umani"][u] + ris["_prob"]["generati"][g]]
        def ranghi(x):
            o = sorted(range(len(x)), key=lambda i: x[i]); rk = [0.0] * len(x)
            for pos, i in enumerate(o): rk[i] = pos
            return rk
        ra, rb = ranghi(a), ranghi(b)
        m = [(x + y) / 2 for x, y in zip(ra, rb)]
        nu = len(rif["_punteggi"]["umani"][u])
        conf[chiave] = round(auc(m[:nu], m[nu:]), 4)
    return {"confronti": conf, "auc_media": round(statistics.fmean(conf.values()), 4)}


def extra(clf) -> dict:
    out = {}
    acc_u = [leggi(f) for f in sorted((C / "accademico").glob("acc_*.txt"))]
    acc_g = [leggi(f) for f in txt(C / "tara-acc/ia")]
    if acc_u and acc_g:
        pu, pg = clf.prob(acc_u), clf.prob(acc_g)
        out["accademico"] = {"auc": round(auc([1 - p for p in pu], [1 - p for p in pg]), 4), "umani": len(acc_u), "generati": len(acc_g),
                             "umani_sopra_05": sum(p >= 0.5 for p in pu), "generati_sopra_05": sum(p >= 0.5 for p in pg)}
    letture = {"1": C / "lettura-cieca", "2": C / "lettura-cieca-2", "3": C / "lettura-cieca-3", "4": C / "lettura-cieca-4",
               "4b": C / "lettura-cieca-4b", "5A": C / "lettura-cieca-5/A", "5B": C / "lettura-cieca-5/B",
               "6A": C / "lettura-cieca-6/A", "6P": C / "lettura-cieca-6/P"}
    out["riscritture"] = {}
    for k, d in letture.items():
        nomi = [f.name for f in sorted((d / "orig").glob("*.txt")) if (d / "riscritti" / f.name).exists()]
        po = clf.prob([leggi(d / "orig" / n) for n in nomi]); pr = clf.prob([leggi(d / "riscritti" / n) for n in nomi])
        out["riscritture"][k] = {"testi": len(nomi), "mediana_prima": round(statistics.median(po), 4), "mediana_dopo": round(statistics.median(pr), 4),
                                 "sotto_05_prima": sum(p < 0.5 for p in po), "sotto_05_dopo": sum(p < 0.5 for p in pr)}
    casi = {"c03 lettura 1, originale": C / "lettura-cieca/orig/c03.txt", "c03 lettura 1, riscritto (Pangram IA 100%)": C / "lettura-cieca/riscritti/c03.txt",
            "o02 lettura 6, originale (GPTZero IA 100%)": C / "lettura-cieca-6/A/orig/o02.txt", "o02 lettura 6, riscritto (GPTZero IA 100%)": C / "lettura-cieca-6/A/riscritti/o02.txt"}
    out["casi_esterni"] = {k: round(clf.prob([leggi(p)])[0], 4) for k, p in casi.items()}
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo-base", action="store_true")
    ap.add_argument("--uscita", help="nome del file in risultati/ (per le prove che non contano)")
    ap.add_argument("--salva", action="store_true", help="salva il modello addestrato in modello-addestrato/")
    a = ap.parse_args(argv)
    coppie, tr, va = dati_addestramento()
    esempi = [(u, 0) for _, u, _, _, _ in tr] + [(g, 1) for _, _, g, _, _ in tr]
    umani, generati = dati_verifica()
    print(f"coppie {len(coppie)} (addestramento {len(tr)}, validazione {len(va)}) · verifica: umani "
          + ", ".join(f"{k} {len(v)}" for k, v in umani.items()) + " · generati " + ", ".join(f"{k} {len(v)}" for k, v in generati.items()), flush=True)
    escluse = (D / "escluse.txt").read_text(encoding="utf-8").split() if (D / "escluse.txt").exists() else []
    esito = {"coppie": len(coppie), "addestramento": len(tr), "validazione": len(va), "escluse": escluse}
    rif = detect_riferimento(umani, generati)
    esito["detect_py"] = {k: v for k, v in rif.items() if not k.startswith("_")}
    print("detect.py: AUC media", rif["auc_media"], flush=True)
    base = Base(); base.addestra(esempi)
    rb = verifica("tfidf", base, va, umani, generati)
    esito["base_tfidf"] = {k: v for k, v in rb.items() if not k.startswith("_")}
    esito["base_tfidf"]["extra"] = extra(base)
    print("TF-IDF: AUC media", rb["auc_media"], "· umani giudicati generati", rb["umani_giudicati_generati"]["quota"], flush=True)
    if not a.solo_base:
        bert = Bert(); bert.addestra(esempi)
        r = verifica("bert", bert, va, umani, generati)
        esito["bert"] = {k: v for k, v in r.items() if not k.startswith("_")}
        esito["bert"]["combinazione_con_detect"] = combinazione(rif, r)
        esito["bert"]["extra"] = extra(bert)
        c1 = r["auc_media"] >= rif["auc_media"] and r["auc_minima"] >= 0.85
        c2 = r["umani_giudicati_generati"]["quota"] <= 0.03
        esito["criteri"] = {"1_riconoscimento": c1, "2_falsi_allarmi": c2,
                            "esito": "REGGE" if c1 and c2 else "REGGE IN PARTE" if c1 else "NON REGGE"}
        print("BERT: AUC media", r["auc_media"], "minima", r["auc_minima"], "· umani giudicati generati", r["umani_giudicati_generati"]["quota"],
              "·", esito["criteri"]["esito"], flush=True)
        if a.salva:
            bert.model.save_pretrained(str(D / "modello-addestrato"), safe_serialization=True)
            bert.tok.save_pretrained(str(D / "modello-addestrato"))
            (D / "risultati/probabilita_bert_riaddestrato.json").write_text(json.dumps(r["_prob"], indent=0), encoding="utf-8")
        if not a.uscita:
            (D / "risultati/probabilita_bert.json").write_text(json.dumps(r["_prob"], indent=0), encoding="utf-8")
    nome = a.uscita or ("esito_base.json" if a.solo_base else "esito.json")
    (D / "risultati" / nome).write_text(json.dumps(esito, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
