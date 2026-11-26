"""Test della revisione di SLOP (1.4.0): le voci che non distinguono non contano nel punteggio, la pulizia non cambia."""
import sys
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "skills" / "umanizza"))

import detect  # noqa: E402
import humanize as H  # noqa: E402
import lessico as L  # noqa: E402

DATI = L.carica()
TESTO = ("La riunione è stata breve. Tuttavia abbiamo deciso molte cose. Inoltre il gruppo ha scelto la data, "
         "pertanto il lavoro comincia lunedì alle 9 in via Roma 12 con Anna e Marco.")


class TestSlopDev(unittest.TestCase):
    def test_sedici_voci_non_contano(self):
        escluse = [v.voce for v in DATI["voci"] if not v.conta]
        self.assertEqual(len(escluse), 16)
        for v in ("inoltre", "tuttavia", "pertanto", "infatti"):
            self.assertIn(v, escluse)

    def test_registro_non_abbassa_slop(self):
        self.assertEqual(detect.analizza(TESTO, DATI).controlli["slop"]["punteggio"], 100.0)

    def test_voci_che_distinguono_contano(self):
        t = "In un mondo sempre più digitale, " + TESTO
        self.assertLess(detect.analizza(t, DATI).controlli["slop"]["punteggio"], 100.0)

    def test_il_report_le_segnala_ancora(self):
        lessico = [s for s in H.umanizza(TESTO, DATI).segnalazioni if s.tipo == "lessico"]
        self.assertGreaterEqual(len(lessico), 3)



class TestImpronta(unittest.TestCase):
    """1.6.0: le lineette come inciso si riportano ma non tolgono punti; gli invisibili sì."""

    def test_lineette_non_pesano(self):
        r = detect.analizza("Il progetto è partito a marzo — dopo due mesi di prove — con 12 persone a Torino. " * 3, DATI)
        self.assertEqual(r.controlli["impronta"]["punteggio"], 100.0)
        self.assertIn("lineette", r.controlli["impronta"]["dettaglio"])

    def test_invisibili_pesano(self):
        r = detect.analizza("Il progetto è partito a marzo\u200b con 12 persone a Torino e Milano. " * 3, DATI)
        self.assertLess(r.controlli["impronta"]["punteggio"], 100.0)

if __name__ == "__main__":
    unittest.main()
