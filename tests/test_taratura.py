"""Test della taratura con export sintetici nei formati di Meta, LinkedIn e X."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "skills" / "umanizza"))

import detect  # noqa: E402
import lessico as L  # noqa: E402
import taratura as T  # noqa: E402

POST = (
    "Ieri ho spostato il database del gestionale su un server nuovo con 64 GB di RAM. "
    "La migrazione è durata quattro ore, tre delle quali a capire perché MySQL rifiutava "
    "le connessioni dal vecchio IP. Alla fine era una riga nel file di configurazione. Numero {n}."
)


def _mojibake(s: str) -> str:
    return s.encode("utf-8").decode("latin-1")


def scrivi_export(base: Path) -> list[Path]:
    """Un export per piattaforma, con il formato reale dei file."""
    meta = base / "meta.zip"
    with zipfile.ZipFile(meta, "w") as z:
        threads = {"text_post_app_text_posts": [{"media": [{"title": _mojibake(POST.format(n=f"T{i}")), "creation_timestamp": 1600000000 + i}]} for i in range(25)]}
        z.writestr("your_instagram_activity/threads/threads_and_replies.json", json.dumps(threads))
        ig = [{"media": [{"uri": "x.jpg", "creation_timestamp": 1600000000, "title": _mojibake(POST.format(n=f"I{i}"))}]} for i in range(22)]
        z.writestr("your_instagram_activity/content/posts_1.json", json.dumps(ig))
        fb = [{"timestamp": 1500000000 + i, "data": [{"post": _mojibake(POST.format(n=f"F{i}"))}]} for i in range(21)]
        z.writestr("your_facebook_activity/posts/your_posts__check_ins__photos_and_videos_1.json", json.dumps(fb))
        z.writestr("your_instagram_activity/comments/post_comments_1.json", json.dumps([{"string_map_data": {"Comment": {"value": "commento da non prendere " * 10}}}]))
    li = base / "Shares.csv"
    righe = ["Date,ShareLink,ShareCommentary,SharedUrl,MediaUrl,Visibility"]
    for i in range(20):
        righe.append(f'2021-03-0{i % 9 + 1} 10:00:00,https://lnkd.in/x,"{POST.format(n=f"L{i}")}",,,MEMBER_NETWORK')
    li.write_text("\n".join(righe), encoding="utf-8")
    x = base / "tweets.js"
    tw = [{"tweet": {"full_text": POST.format(n=f"X{i}"), "created_at": "Wed Oct 10 20:19:24 +0000 2018"}} for i in range(20)]
    tw.append({"tweet": {"full_text": "RT @qualcuno: " + POST.format(n="RT"), "created_at": "Wed Oct 10 20:19:24 +0000 2018"}})
    x.write_text("window.YTD.tweets.part0 = " + json.dumps(tw), encoding="utf-8")
    return [meta, li, x]


def zitto(fn, *a):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return fn(*a)


class TestTaratura(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.export = scrivi_export(self.base)
        self.cartella = self.base / "tara"

    def tearDown(self):
        self.tmp.cleanup()

    def importa(self, *extra):
        return zitto(T.main, ["importa", *map(str, self.export), "--cartella", str(self.cartella), *extra])

    def test_importa_tutte_le_piattaforme(self):
        self.assertEqual(self.importa(), 0)
        conta = {d.name: len(list(d.glob("*.txt"))) for d in (self.cartella / "umano").iterdir()}
        self.assertEqual(conta, {"threads": 25, "instagram": 22, "facebook": 21, "linkedin": 20, "x": 20})

    def test_ripara_codifica_meta_e_salta_commenti_e_retweet(self):
        self.importa()
        testo = (self.cartella / "umano" / "threads" / "threads_0001.txt").read_text(encoding="utf-8")
        self.assertIn("è durata", testo)
        tutti = " ".join(f.read_text(encoding="utf-8") for f in (self.cartella / "umano").rglob("*.txt"))
        self.assertNotIn("commento da non prendere", tutti)
        self.assertNotIn("RT @", tutti)

    def test_filtro_data(self):
        # Facebook (2017) e X (2018) prima del 2019; Threads e Instagram (2020) e LinkedIn (2021) dopo.
        self.importa("--prima-di", "2019-01-01")
        piattaforme = {d.name for d in (self.cartella / "umano").iterdir()}
        self.assertEqual(piattaforme, {"facebook", "x"})

    def test_consegne_senza_il_post_intero(self):
        self.importa()
        consegne = [json.loads(r) for r in (self.cartella / "consegne.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(consegne), 108)
        self.assertNotIn("configurazione", consegne[0]["prompt"])  # solo l'inizio del post

    def test_misura_e_applica(self):
        self.importa()
        # Gemelli: testi generati veri del corpus, uno per consegna.
        ia = sorted((RADICE / "bench" / "corpus_ia").rglob("*.txt"))
        for i, r in enumerate((self.cartella / "consegne.jsonl").read_text(encoding="utf-8").splitlines()):
            c = json.loads(r)
            d = self.cartella / "ia" / c["piattaforma"]
            d.mkdir(parents=True, exist_ok=True)
            (d / f"{c['id']}_claude.txt").write_text(ia[i % len(ia)].read_text(encoding="utf-8"), encoding="utf-8")
        self.assertEqual(zitto(T.main, ["misura", str(self.cartella)]), 0)
        m = json.loads((self.cartella / "misura.json").read_text(encoding="utf-8"))
        self.assertEqual(m["threads"]["coppie"], 25)
        self.assertGreater(m["threads"]["auc"], 0.5)
        dest = self.base / "taratura.json"
        self.assertEqual(zitto(T.main, ["applica", str(self.cartella), "--salva", str(dest)]), 0)
        t = json.loads(dest.read_text(encoding="utf-8"))
        self.assertLessEqual(t["soglia_passa"], detect.SOGLIA_PASSA)
        self.assertLess(t["soglia_segnalato"], t["soglia_passa"])
        self.assertIn("threads", t["per_piattaforma"])
        # detect usa le soglie personali
        s = detect.carica_soglie(dest, "threads")
        self.assertEqual(s["passa"], t["per_piattaforma"]["threads"]["soglia_passa"])

    def test_soglie_mai_piu_severe_delle_generiche(self):
        p, s = T.soglie_personali([95, 96, 97, 98, 99] * 5, 3)
        self.assertEqual((p, s), (detect.SOGLIA_PASSA, detect.SOGLIA_SEGNALATO))
        p, s = T.soglie_personali([60, 70, 75, 80, 90] * 5, 3)
        self.assertLess(p, detect.SOGLIA_PASSA)
        self.assertLess(s, 60)

    def test_applica_rifiuta_pochi_post(self):
        (self.cartella).mkdir()
        (self.cartella / "misura.json").write_text(json.dumps({"x": {"umani_punteggi": [80] * 5, "ia_punteggi": [], "auc": 0.5}}))
        self.assertEqual(zitto(T.main, ["applica", str(self.cartella), "--salva", str(self.base / "t.json")]), 1)

    def test_cartella_di_txt_per_altri_social(self):
        d = self.base / "tiktok"
        d.mkdir()
        for i in range(3):
            (d / f"{i}.txt").write_text(POST.format(n=i), encoding="utf-8")
        zitto(T.main, ["importa", str(d), "--cartella", str(self.cartella)])
        self.assertEqual(len(list((self.cartella / "umano" / "tiktok").glob("*.txt"))), 3)

    def test_genera_senza_chiave(self):
        import os
        self.importa()
        vecchia = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            self.assertEqual(zitto(T.main, ["genera", str(self.cartella)]), 2)
            self.assertEqual(zitto(T.main, ["genera", str(self.cartella), "--solo-consegne"]), 0)
        finally:
            if vecchia:
                os.environ["ANTHROPIC_API_KEY"] = vecchia


if __name__ == "__main__":
    unittest.main()
