"""Correzioni trovate dalla revisione indipendente del 26/11/2026: intestazione dei comunicati e apostrofi nella fedeltà."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills" / "umanizza"))

import humanize as H  # noqa: E402
import lessico as L  # noqa: E402

DATI = L.carica()


class TestIntestazione(unittest.TestCase):
    def pulisci(self, t):
        return H.umanizza(t, DATI).testo

    def test_segnaposto(self):
        t = "[Città], [data] — [Nome dell'organizzazione] annuncia il lancio della piattaforma."
        self.assertIn("[data] — [Nome", self.pulisci(t))

    def test_data_vera(self):
        t = "Milano, 12 marzo 2026 — L'azienda annuncia il lancio della piattaforma per i comuni."
        self.assertIn("2026 — L'azienda", self.pulisci(t))
        t = "**Roma, 3 novembre** — Il comune apre il nuovo sportello digitale per i cittadini."
        self.assertIn("— Il comune", self.pulisci(t))

    def test_inciso_resta_virgola(self):
        t = "Il progetto — dopo mesi di prove — è partito con dodici persone a Torino."
        self.assertNotIn("—", self.pulisci(t))


class TestFedeltaApostrofi(unittest.TestCase):
    def test_apostrofo_dritto_non_perde_la_citazione(self):
        prima = "Ha scritto: “manca un’ultima modifica al contratto”, e poi ha chiuso."
        dopo = "Ha scritto: \"manca un'ultima modifica al contratto\", e poi ha chiuso."
        self.assertEqual(L.confronta_fatti(prima, dopo)["persi"], [])

    def test_citazione_tolta_resta_persa(self):
        prima = "Ha scritto: «manca un’ultima modifica al contratto», e poi ha chiuso."
        self.assertTrue(L.confronta_fatti(prima, "Ha chiuso senza dire niente.")["persi"])


if __name__ == "__main__":
    unittest.main()
