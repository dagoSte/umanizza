"""Test di bench/indice.py: componenti tra 0 e 1, pesi che sommano a 1, valore del README aggiornato."""
import re
import sys
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "bench"))

import indice as I  # noqa: E402


class TestIndice(unittest.TestCase):
    def test_pesi_e_componenti(self):
        self.assertAlmostEqual(sum(I.PESI.values()), 1.0)
        r = I.calcola()
        for k, v in r["componenti"].items():
            self.assertTrue(0.0 <= v <= 1.0, k)
        self.assertTrue(0.0 <= r["indice"] <= 10.0)

    def test_readme_aggiornato(self):
        valore = I.formatta(I.calcola()["indice"])
        readme = (RADICE / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"**{valore} su 10.**", readme)
        self.assertIn(valore.replace(",", "%2C") + "%20su%2010", readme)  # badge
        self.assertEqual(len(re.findall(r"\*\*\d,\d\d su 10\.\*\*", readme)), 1)


if __name__ == "__main__":
    unittest.main()
