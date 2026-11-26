"""Test di bench/grafici.py: gli otto SVG del README si rigenerano e sono XML valido."""
import contextlib
import io
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RADICE / "bench"))

import grafici  # noqa: E402


class TestGrafici(unittest.TestCase):
    def test_otto_svg_validi(self):
        with tempfile.TemporaryDirectory() as d:
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(grafici.main(["--cartella", d]), 0)
            nomi = sorted(p.name for p in Path(d).glob("*.svg"))
            self.assertEqual(len(nomi), 8)
            for n in nomi:
                ET.parse(Path(d) / n)

    def test_numeri_italiani(self):
        self.assertEqual(grafici.num(0.905), "0,91")


if __name__ == "__main__":
    unittest.main()
