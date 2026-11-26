"""Test di modifiche.py: modifiche puntuali e verifica alla cieca."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "skills" / "umanizza"))

import modifiche as M  # noqa: E402

TESTO = ("In un mondo sempre più veloce, il team ha lavorato tre mesi. Il risultato? Un'app che funziona.\n\n"
         "Inoltre abbiamo ridotto i tempi di consegna del 30%. Grazie a tutti!")
MODS = [{"vecchio": "In un mondo sempre più veloce, il team", "nuovo": "Il team"},
        {"vecchio": "Il risultato? Un'app che funziona.", "nuovo": "Ne è uscita un'app che funziona."},
        {"vecchio": "Inoltre abbiamo", "nuovo": "Abbiamo anche"}]


class TestModifiche(unittest.TestCase):
    def test_applica_tutte_e_lascia_il_resto(self):
        nuovo = M.applica(TESTO, MODS)
        self.assertTrue(nuovo.startswith("Il team ha lavorato tre mesi. Ne è uscita"))
        self.assertIn("Abbiamo anche ridotto i tempi di consegna del 30%. Grazie a tutti!", nuovo)
        self.assertIn("\n\n", nuovo)

    def test_solo_quelle_tenute(self):
        nuovo = M.applica(TESTO, MODS, tenere={2})
        self.assertTrue(nuovo.startswith("In un mondo sempre più veloce"))
        self.assertIn("Ne è uscita", nuovo)
        self.assertIn("Inoltre abbiamo", nuovo)

    def test_errori(self):
        self.assertTrue(M.controlla(TESTO, [{"vecchio": "non c'è", "nuovo": "x"}]))
        self.assertTrue(M.controlla(TESTO + " Il team", [{"vecchio": "team", "nuovo": "x"}]))  # «team» compare due volte
        sovrapposte = [{"vecchio": "il team ha lavorato", "nuovo": "x"}, {"vecchio": "team ha", "nuovo": "y"}]
        self.assertTrue(any("sovrappongono" in e for e in M.controlla(TESTO, sovrapposte)))
        self.assertEqual(M.controlla(TESTO, MODS), [])

    def test_prova_alla_cieca(self):
        foglio, mappa = M.prova(TESTO, MODS)
        self.assertEqual(len(mappa), 3)
        self.assertIn("## Modifica 2", foglio)
        self.assertIn("Il risultato? Un'app che funziona.", foglio)
        self.assertIn("Ne è uscita un'app che funziona.", foglio)
        # scegliere sempre la versione nuova tiene tutto; scegliere l'originale o pari non tiene niente
        nuove = {k: ("X" if v["X"] == "nuovo" else "Y") for k, v in mappa.items()}
        vecchie = {k: ("Y" if v["X"] == "nuovo" else "X") for k, v in mappa.items()}
        self.assertEqual(M.da_tenere(nuove, mappa), {1, 2, 3})
        self.assertEqual(M.da_tenere(vecchie, mappa), set())
        self.assertEqual(M.da_tenere({"1": "pari", "2": "pari", "3": "pari"}, mappa), set())

    def test_cli(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            (d / "pulito.txt").write_text(TESTO, encoding="utf-8")
            (d / "modifiche.json").write_text(json.dumps(MODS, ensure_ascii=False), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(M.main(["prova", str(d / "pulito.txt"), str(d / "modifiche.json"), "-o", str(d / "confronto.md")]), 0)
            mappa = json.loads((d / "confronto.json").read_text())
            scelte = {k: ("X" if v["X"] == "nuovo" else "Y") if k == "1" else "pari" for k, v in mappa.items()}
            (d / "scelte.json").write_text(json.dumps(scelte), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(M.main(["applica", str(d / "pulito.txt"), str(d / "modifiche.json"),
                                         "--scelte", str(d / "scelte.json"), "-o", str(d / "riscritto.txt")]), 0)
            r = (d / "riscritto.txt").read_text(encoding="utf-8")
            self.assertTrue(r.startswith("Il team ha lavorato"))
            self.assertIn("Il risultato?", r)
            (d / "male.json").write_text(json.dumps([{"vecchio": "assente", "nuovo": "x"}]), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(M.main(["applica", str(d / "pulito.txt"), str(d / "male.json"), "-o", str(d / "x.txt")]), 1)


if __name__ == "__main__":
    unittest.main()
