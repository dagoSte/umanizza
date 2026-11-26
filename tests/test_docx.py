"""Test di docx.py: revisioni tracciate su file Word, con verifiche. Solo libreria standard."""
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

import docx as X  # noqa: E402

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
DOC = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document {W}><w:body>'
    '<w:p><w:r><w:t xml:space="preserve">Nel 1929 l’autrice conosce Valli a Torino. </w:t></w:r>'
    '<w:r><w:rPr><w:i/></w:rPr><w:t>Il quaderno blu</w:t></w:r>'
    '<w:r><w:t xml:space="preserve"> è difficile da classificare: sta tra tre generi diversi.</w:t></w:r>'
    '<w:r><w:rPr><w:rStyle w:val="FootnoteReference"/></w:rPr><w:footnoteReference w:id="1"/></w:r>'
    '<w:r><w:t xml:space="preserve"> Il confronto resta introduttivo e generico.</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>Un oggetto, un nome o un odore fanno tornare un ricordo.</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>La casa era piena di gente (QB, p. 8).</w:t></w:r></w:p>'
    '</w:body></w:document>'
)
NOTE = (
    f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:footnotes {W}>'
    '<w:footnote w:id="1"><w:p><w:r><w:t>Si cita dall’edizione effettivamente utilizzata.</w:t></w:r></w:p></w:footnote>'
    '</w:footnotes>'
)


def crea_docx(cartella: Path) -> Path:
    p = cartella / "prova.docx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", DOC)
        z.writestr("word/footnotes.xml", NOTE)
    return p


MODIFICHE = [
    {"id": "generi", "vecchio": " è difficile da classificare: sta tra tre generi diversi.", "nuovo": " è difficile da classificare."},
    {"id": "frase tolta", "vecchio": "Un oggetto, un nome o un odore fanno tornare un ricordo.", "nuovo": None},
    {"id": "nota", "parte": "note", "vecchio": " effettivamente utilizzata.", "nuovo": " Losada, 1970."},
    {"id": "apostrofo", "vecchio": "l'autrice conosce", "nuovo": "l'autrice incontra"},
]


class TestDocx(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        self.src = crea_docx(self.d)

    def tearDown(self):
        self.tmp.cleanup()

    def test_estrai(self):
        t = X.estrai(self.src)
        self.assertIn("Il quaderno blu è difficile da classificare", t)
        self.assertNotIn("edizione", t)
        self.assertIn("edizione effettivamente utilizzata", X.estrai(self.src, note=True))

    def test_revisioni_tracciate(self):
        out = self.d / "rev.docx"
        esito = X.applica(self.src, MODIFICHE, out)
        self.assertEqual([e["esito"] for e in esito["modifiche"]], ["ok"] * 4)
        doc = zipfile.ZipFile(out).read("word/document.xml").decode()
        self.assertIn("<w:ins ", doc)
        self.assertIn("<w:del ", doc)
        self.assertIn('w:author="umanizza"', doc)
        self.assertIn("<w:i/>", doc)
        self.assertEqual(doc.count("<w:footnoteReference"), 1)

    def test_verifiche_passano(self):
        esito = X.applica(self.src, MODIFICHE, self.d / "rev.docx")
        v = esito["verifiche"]
        self.assertTrue(v["xml"])
        self.assertTrue(v["rifiuta_uguale_originale"])
        self.assertEqual(v["note_spostate"], [])
        self.assertIn("Losada", X.estrai(self.d / "rev.docx", note=True))
        self.assertIn("1929", X.estrai(self.d / "rev.docx"))

    def test_accettate(self):
        out = self.d / "acc.docx"
        X.applica(self.src, MODIFICHE, out, accettate=True)
        doc = zipfile.ZipFile(out).read("word/document.xml").decode()
        self.assertNotIn("<w:ins ", doc)
        self.assertNotIn("<w:del ", doc)
        t = X.estrai(out)
        self.assertNotIn("Un oggetto", t)
        self.assertIn("l’autrice incontra", t)

    def test_modifica_ambigua_non_applicata(self):
        esito = X.applica(self.src, [{"id": "ambigua", "vecchio": "a", "nuovo": "b"}], self.d / "x.docx")
        self.assertEqual(esito["modifiche"][0]["esito"], "NON APPLICATA")

    def test_nota_spostata_segnalata(self):
        mod = [{"id": "taglio", "vecchio": " è difficile da classificare: sta tra tre generi diversi.", "nuovo": ""}]
        esito = X.applica(self.src, mod, self.d / "x.docx")
        self.assertEqual([n["nota"] for n in esito["verifiche"]["note_spostate"]], ["1"])

    def test_fatti_persi_segnalati(self):
        mod = [{"id": "data", "vecchio": "Nel 1929 l’autrice", "nuovo": "L’autrice"}]
        esito = X.applica(self.src, mod, self.d / "x.docx")
        self.assertIn("1929", esito["verifiche"]["fedelta"]["persi"])

    def test_due_richiami_attaccati_contano_due(self):
        doc = (f'<w:document {W}><w:body><w:p><w:r><w:t>Uno nel 1944.</w:t></w:r><w:r><w:footnoteReference w:id="60"/>'
               '<w:footnoteReference w:id="63"/></w:r><w:r><w:t xml:space="preserve"> Due.</w:t></w:r>'
               '<w:r><w:footnoteReference w:id="65"/></w:r></w:p></w:body></w:document>')
        note = X._frase_prima_delle_note(doc)
        self.assertEqual(sorted(note), ["1", "2", "3"])  # come in Word: 1944.¹² Due.³
        self.assertEqual(note["3"], "Due.")

    def test_cli(self):
        m = self.d / "m.json"
        m.write_text(json.dumps(MODIFICHE), encoding="utf-8")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            codice = X.main(["applica", str(self.src), str(m), "-o", str(self.d / "r.docx")])
        self.assertEqual(codice, 0)
        self.assertIn("rifiutando tutto", buf.getvalue())

    def test_cli_esce_con_1_se_una_modifica_non_si_applica(self):
        m = self.d / "m.json"
        m.write_text(json.dumps([{"id": "x", "vecchio": "frase che non esiste", "nuovo": "y"}]), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(X.main(["applica", str(self.src), str(m), "-o", str(self.d / "r.docx")]), 1)


if __name__ == "__main__":
    unittest.main()
