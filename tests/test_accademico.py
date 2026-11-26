"""Test di umanizza 1.2: modalità accademica, mappa delle frasi, domande per l'autore, brief prima di scrivere.

Solo libreria standard: python3 -m unittest discover tests
"""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
SKILL = RADICE / "skills" / "umanizza"
sys.path.insert(0, str(SKILL))

import detect  # noqa: E402
import humanize as H  # noqa: E402
import lessico as L  # noqa: E402

DATI = L.carica()

CITAZIONI = (
    "La critica ha studiato a lungo il romanzo (Rossi, 2019; Bianchi, 2018). Il tema della memoria torna spesso "
    "nel libro (QB, p. 8) e ritorna nelle pagine finali (QB, pp. 18-19). Secondo la lettura più diffusa il libro "
    "parla di memoria (Verdi, 2020, p. 45) e di esilio (Neri et al., 2017), cioè di quello che resta a chi parte."
)
PROSA = (
    "Il libro racconta una vita lunga e difficile, segnata dalla guerra e da molti viaggi. La scrittura cerca di "
    "trattenere i ricordi e di darli a chi legge, anche quando la memoria comincia a mancare e le pagine si fanno "
    "più brevi e più fragili."
)


def triadi(testo, **kw):
    return [t for t in L.trova_tell(testo, **kw) if t.id == "triade"]


class TestModalitaAccademica(unittest.TestCase):
    def concretezza(self, testo, genere=None):
        return detect.analizza(testo, DATI, genere=genere).controlli["concretezza"]["punteggio"]

    def test_citazioni_non_contano_in_concretezza(self):
        self.assertGreater(self.concretezza(CITAZIONI), self.concretezza(CITAZIONI, "accademico"))

    def test_prosa_senza_citazioni_invariata(self):
        self.assertEqual(self.concretezza(PROSA), self.concretezza(PROSA, "accademico"))

    def test_stesso_denominatore(self):
        a = detect.analizza(CITAZIONI, DATI)
        b = detect.analizza(CITAZIONI, DATI, genere="accademico")
        self.assertEqual(a.parole, b.parole)

    def test_apparato_tolto(self):
        resto = L.togli_apparato(CITAZIONI)
        for via in ("Rossi, 2019", "Bianchi, 2018", "QB, p. 8", "QB, pp. 18-19", "Verdi, 2020, p. 45", "Neri et al., 2017"):
            self.assertNotIn(via, resto)
        self.assertIn("memoria", resto)

    def test_date_e_titoli_non_sono_apparato(self):
        t = "Nasce a Torino il 31 ottobre 1903 e pubblica Il quaderno blu (1928). Nel 1929 conosce Valli. Nell'aprile 1977 torna."
        self.assertEqual(L.togli_apparato(t), t)

    def test_triadi_fattuali_non_contano(self):
        t = "Visse tra Torino, Milano e Genova. Poi abitò tra Roma, Parigi e Berlino. Scrisse nel 1928, nel 1930 e nel 1941."
        self.assertEqual(len(triadi(t)), 2)
        self.assertEqual(len(triadi(t, accademico=True)), 0)

    def test_triadi_retoriche_contano_ancora(self):
        t = "Il metodo è veloce, semplice e sicuro. Il risultato è chiaro, utile e duraturo. Il gruppo è unito, motivato e pronto."
        self.assertEqual(len(triadi(t, accademico=True)), 2)

    def test_cli_genere(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.txt"
            f.write_text(CITAZIONI, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                detect.main([str(f), "--json", "--generico", "--genere", "accademico"])
            self.assertEqual(json.loads(buf.getvalue())["genere"], "accademico")


class TestMappa(unittest.TestCase):
    TESTO = (
        "Il libro racconta una vita lunga, rendendo visibile la memoria dell'esilio. "
        "La realizzazione della documentazione richiede l'organizzazione e la valutazione delle fonti. "
        "Inoltre il testo usa molte citazioni dirette. "
        "È importante sottolineare che l'autrice scrive lontano da casa. "
        "La casa era piena di gente e di voci."
    )

    def test_quattro_costrutti(self):
        per_frase = {" ".join(m["frase"].split()[:2]): set(m["motivi"]) for m in detect.mappa(self.TESTO)}
        self.assertIn("gerundio", per_frase["Il libro"])
        self.assertIn("nominalizzazioni", per_frase["La realizzazione"])
        self.assertIn("connettivo", per_frase["Inoltre il"])
        self.assertIn("impersonale", per_frase["È importante"])

    def test_frase_pulita_in_fondo(self):
        m = detect.mappa(self.TESTO)
        self.assertEqual(m[-1]["frase"], "La casa era piena di gente e di voci.")
        self.assertEqual(m[-1]["punti"], 0)

    def test_nominalizzazioni(self):
        m = detect.mappa("La realizzazione della documentazione richiede l'organizzazione e la valutazione delle fonti.")
        self.assertIn("nominalizzazioni", m[0]["motivi"])

    def test_connettivo_intero(self):
        m = detect.mappa("Del resto, in quel libro è lei a raccontare la guerra.")
        self.assertEqual(m[0]["dettagli"], ["Del resto"])

    def test_niente_avverbi_e_nomi_propri_tra_le_nominalizzazioni(self):
        m = detect.mappa("La Generazione del 27 non lavora abbastanza sulla distanza.")
        self.assertNotIn("nominalizzazioni", m[0]["motivi"])

    def test_quando_non_e_gerundio(self):
        m = detect.mappa("Il libro finisce, quando arriva la primavera, con una lettera alla figlia.")
        self.assertNotIn("gerundio", m[0]["motivi"])

    def test_cli_mappa(self):
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / "t.txt"
            f.write_text(self.TESTO, encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                detect.main([str(f), "--mappa", "--generico"])
            self.assertIn("MAPPA", buf.getvalue())


class TestDomande(unittest.TestCase):
    def test_ogni_tell_ha_una_domanda(self):
        d = json.loads((SKILL / "slop.json").read_text(encoding="utf-8"))
        for t in d["tell"]:
            self.assertTrue(t.get("domanda"), f"tell {t['id']} senza domanda")

    def test_ogni_categoria_ha_una_domanda(self):
        d = json.loads((SKILL / "slop.json").read_text(encoding="utf-8"))
        for cat in {v["cat"] for v in d["lessico"]}:
            self.assertTrue(d["domande"].get(cat), f"categoria {cat} senza domanda")

    def test_report_porta_le_domande(self):
        t = "Non è solo uno strumento, è un alleato. Inoltre il metodo è veloce, semplice e sicuro, chiaro, utile e bello."
        esito = H.umanizza(t, DATI)
        self.assertTrue(esito.segnalazioni)
        for s in esito.segnalazioni:
            self.assertTrue(s.domanda, f"segnalazione senza domanda: {s}")


class TestTaraturaAccademica(unittest.TestCase):
    def test_consegna_di_genere(self):
        import taratura as T
        c = T._consegna("accademico_0001", "accademico", "La critica ha letto il romanzo come un libro di memoria. " * 5)
        self.assertIn("tesi di laurea", c["prompt"])
        self.assertNotIn("post", c["prompt"])

    def test_misura_usa_il_genere(self):
        import taratura as T
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "accademico"
            p.mkdir()
            (p / "a.txt").write_text(CITAZIONI, encoding="utf-8")
            r = T._punteggi(Path(d), DATI)["accademico"]["a"]
            self.assertEqual(r.genere, "accademico")


class TestFedelta(unittest.TestCase):
    PRIMA = ("Nel 1929 Anna Ferri conosce Paolo Valli (Rossi, 2019, p. 45) a Torino. "
             "Il biglietto costava 12 euro. Scrive: «Ho cambiato casa troppe volte per sentirmi a casa».")

    def test_fatti_persi(self):
        dopo = "Anna Ferri conosce Valli a Torino. Il biglietto costava poco."
        persi = L.confronta_fatti(self.PRIMA, dopo)["persi"]
        for f in ("1929", "Rossi", "2019", "45", "12", "Paolo", "«Ho cambiato casa troppe volte per sentirmi a casa»"):
            self.assertIn(f, persi)
        self.assertNotIn("Torino", persi)

    def test_riscrittura_fedele(self):
        dopo = ("Anna Ferri incontra Paolo Valli a Torino nel 1929 (Rossi, 2019, p. 45). "
                "Il biglietto costava 12 euro. Scrive: «Ho cambiato casa troppe volte per sentirmi a casa».")
        self.assertEqual(L.confronta_fatti(self.PRIMA, dopo)["persi"], [])

    def test_quota_cambiata(self):
        self.assertEqual(L.confronta_fatti(self.PRIMA, self.PRIMA)["cambiato"], 0.0)
        self.assertGreater(L.confronta_fatti(self.PRIMA, "Tutt'altro testo, senza niente in comune con il primo.")["cambiato"], 0.5)

    def test_cli_mostra_fedelta(self):
        with tempfile.TemporaryDirectory() as d:
            a, b = Path(d) / "a.txt", Path(d) / "b.txt"
            a.write_text(self.PRIMA, encoding="utf-8")
            b.write_text("Anna Ferri conosce Valli a Torino. Il biglietto costava poco.", encoding="utf-8")
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                detect.main([str(a), str(b), "--generico"])
            self.assertIn("FEDELTÀ", buf.getvalue())
            self.assertIn("1929", buf.getvalue())


class TestBrief(unittest.TestCase):
    def test_brief_esiste_ed_e_citato(self):
        brief = SKILL / "prima-di-scrivere.md"
        self.assertTrue(brief.exists())
        self.assertIn("prima-di-scrivere.md", (SKILL / "SKILL.md").read_text(encoding="utf-8"))

    def test_brief_non_contiene_slop(self):
        brief = (SKILL / "prima-di-scrivere.md").read_text(encoding="utf-8")
        regole = brief.split("## Esempi da evitare")[0]
        self.assertEqual([c.testo for c in L.trova_lessico(regole, DATI["voci"]) if c.voce.peso >= 1], [])


if __name__ == "__main__":
    unittest.main()
