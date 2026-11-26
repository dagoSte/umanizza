"""Test di bench/prepara_web.py: genere dall'URL e filtri di qualità, senza rete."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "bench"))

import prepara_web as W  # noqa: E402

PROSA = ("Il nostro studio lavora da vent'anni con le aziende del territorio. Seguiamo progetti piccoli e grandi. "
         "Ogni cliente ha un referente unico che conosce la sua storia. Lavoriamo su appuntamento in via Garibaldi. "
         "Chiamateci per un primo incontro senza impegno. ") * 3


class TestPreparaWeb(unittest.TestCase):
    def test_genere_dal_percorso(self):
        self.assertEqual(W.genere("https://www.esempio.it/blog/un-post"), "blog")
        self.assertEqual(W.genere("https://esempio.it/chi-siamo"), "azienda")
        self.assertEqual(W.genere("https://esempio.it/servizi/consulenza"), "servizi")
        self.assertIsNone(W.genere("https://blog.esempio.it/"))  # il dominio non conta, solo il percorso

    def test_filtri(self):
        self.assertTrue(W.passa(PROSA, "2019-05-01T00:00:00Z"))
        self.assertFalse(W.passa(PROSA, "2022-05-01T00:00:00Z"))
        self.assertFalse(W.passa(PROSA + " Questo sito usa i cookie.", "2019-05-01T00:00:00Z"))
        self.assertFalse(W.passa("Troppo corto. Davvero.", "2019-05-01T00:00:00Z"))

    def test_menu_scartati(self):
        menu = "\n".join(["Home", "Servizi", "Contatti", "Chi siamo"] * 10) + "\n" + PROSA
        self.assertFalse(W.passa(menu, "2019-05-01T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
