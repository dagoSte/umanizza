"""Test di umanizza. Solo libreria standard: python3 -m unittest discover tests"""
import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
SKILL = RADICE / "skills" / "umanizza"
sys.path.insert(0, str(SKILL))

import detect  # noqa: E402
import humanize as H  # noqa: E402
import lessico as L  # noqa: E402

DATI = L.carica()


def pulisci(t, **kw):
    return H.umanizza(t, DATI, **kw).testo


class TestLessicoValido(unittest.TestCase):
    def test_json_e_regex_compilano(self):
        d = json.loads((SKILL / "slop.json").read_text(encoding="utf-8"))
        self.assertGreater(len(d["lessico"]), 200)
        for e in d["lessico"]:
            self.assertIn("voce", e)
            self.assertIn("cat", e)
            self.assertIn("sostituisci", e)

    def test_voci_uniche(self):
        voci = [v.voce for v in DATI["voci"]]
        self.assertEqual(len(voci), len(set(voci)), "voci duplicate nel lessico")

    def test_ogni_tell_rilevato_ha_una_descrizione(self):
        testo = (RADICE / "bench" / "esempi" / "peggiore.txt").read_text(encoding="utf-8")
        for t in L.trova_tell(testo):
            self.assertIn(t.id, DATI["tell"], f"tell {t.id} senza voce in slop.json")


class TestInvisibili(unittest.TestCase):
    def test_toglie_larghezza_zero(self):
        self.assertEqual(pulisci("cia​o a⁠ tutti﻿"), "ciao a tutti")

    def test_spazio_indivisibile_diventa_spazio(self):
        self.assertEqual(pulisci("10 euro"), "10 euro")

    def test_spazio_indivisibile_dopo_p_e_pp_resta(self):
        t = "(QB, p.\u00a08; pp.\u00a018-19; p.\u202f5)"
        self.assertEqual(H.umanizza(t, DATI, passate=("invisibili",)).testo, t)

    def test_spazio_indivisibile_dopo_parola_in_p_tolto(self):
        t = "Fine del loop.\u00a0Poi il cap.\u00a03."
        self.assertEqual(H.umanizza(t, DATI, passate=("invisibili",)).testo, "Fine del loop. Poi il cap. 3.")

    def test_non_rompe_emoji_con_zwj(self):
        famiglia = "👨‍👩‍👧"
        self.assertEqual(pulisci(f"la mia {famiglia} oggi"), f"la mia {famiglia} oggi")

    def test_non_rompe_bandiera_con_tag(self):
        scozia = "\U0001F3F4\U000E0067\U000E0062\U000E0073\U000E0063\U000E0074\U000E007F"
        self.assertEqual(pulisci(f"forza {scozia}"), f"forza {scozia}")

    def test_toglie_tag_fuori_dalle_bandiere(self):
        self.assertEqual(pulisci("ciao\U000E0041\U000E0042"), "ciao")


class TestTipografia(unittest.TestCase):
    def test_lineetta_inciso_diventa_virgola(self):
        self.assertEqual(pulisci("Il codice — scritto ieri — funziona."), "Il codice, scritto ieri, funziona.")

    def test_lineetta_dialogo_resta(self):
        t = "— Dove vai? — chiese Marco."
        self.assertTrue(pulisci(t).startswith("— Dove vai?"))

    def test_intervallo_numerico(self):
        self.assertEqual(pulisci("dalle 10–12"), "dalle 10-12")

    def test_virgolette_curve_e_caporali(self):
        self.assertEqual(pulisci("“ciao” e l’altro, «questo» resta"), "\"ciao\" e l'altro, «questo» resta")

    def test_puntini(self):
        self.assertEqual(pulisci("vediamo…"), "vediamo...")


class TestLessico(unittest.TestCase):
    def test_apertura_tolta_e_maiuscola(self):
        self.assertEqual(
            pulisci("In un mondo sempre più digitale, le aziende devono cambiare."),
            "Le aziende devono cambiare.",
        )

    def test_connettivo_tolto_e_maiuscola(self):
        self.assertEqual(pulisci("È importante sottolineare che il test passa."), "Il test passa.")

    def test_non_rompe_la_negazione(self):
        self.assertEqual(pulisci("Non è chiaro che cosa succeda."), "Non è chiaro che cosa succeda.")

    def test_burocratese(self):
        self.assertEqual(pulisci("Al fine di risparmiare, usiamo Redis."), "Per risparmiare, usiamo Redis.")

    def test_conserva_maiuscola_iniziale(self):
        self.assertEqual(pulisci("Allo scopo di testare, gira tutto."), "Per testare, gira tutto.")

    def test_registro_e_articoli_non_toccati(self):
        # Cambiano registro o accordo: solo segnalati.
        for t in ["Tuttavia, mancano i dati.", "Pertanto la richiesta è respinta.", "È un vero e proprio sbaglio."]:
            self.assertEqual(pulisci(t), t)

    def test_fondamentale_non_viene_toccato(self):
        # In fisica e in diritto è un termine tecnico: solo segnalato.
        t = "Le quattro forze fondamentali della natura."
        self.assertEqual(pulisci(t), t)

    def test_codice_e_url_protetti(self):
        t = "Usa `al fine di` e https://es.it/al-fine-di per il test."
        self.assertEqual(pulisci(t), t)

    def test_blocco_di_codice_protetto(self):
        t = "Ecco:\n```\n# Al fine di testare — tutto\nx = 1\n```\n"
        self.assertEqual(pulisci(t), t)

    def test_niente_spazio_orfano_a_inizio_riga(self):
        out = pulisci("Ciao.\n\nIn conclusione, il futuro è adesso.")
        self.assertEqual(out, "Ciao.\n\nIl futuro è adesso.")

    def test_inciso_tolto_a_meta_frase(self):
        self.assertEqual(pulisci("Il progetto, in conclusione, funziona."), "Il progetto funziona.")

    def test_idempotente(self):
        t = (RADICE / "bench" / "esempi" / "peggiore.txt").read_text(encoding="utf-8")
        una = pulisci(t)
        self.assertEqual(pulisci(una), una)


class TestRegressioniRevisione(unittest.TestCase):
    """Ogni caso qui è un bug trovato dalla revisione indipendente."""

    def invariato(self, t):
        self.assertEqual(pulisci(t), t)

    def test_negazione_lontana(self):
        self.invariato("Non mi è chiaro che cosa vuoi.")

    def test_cancellazione_solo_a_inizio_frase(self):
        self.invariato("Gli va detto che domani non c'è scuola.")
        self.invariato("Viviamo in un mondo sempre più caldo e affollato.")
        self.invariato("La sua posizione nel panorama attuale del mercato è debole.")

    def test_congiuntivo_senza_reggente(self):
        self.invariato("È innegabile che il clima sia cambiato. Non c'è dubbio che abbia ragione lui.")

    def test_verbi_in_senso_proprio(self):
        self.invariato("Riassumendo il libro, ho capito molte cose.")
        self.invariato("Ci vuole un anno per concludere il progetto.")
        self.invariato("Lo dico in sintesi.")
        self.invariato("Dobbiamo realizzare che abbiamo sbagliato.")
        self.invariato("Il progetto si pone come obiettivo la sostenibilità.")
        self.invariato("La telecamera ruota a 360 gradi.")

    def test_grassetto_non_svuotato(self):
        self.invariato("* **In conclusione**, il test è passato.")

    def test_testo_tecnico_non_toccato(self):
        self.invariato("Aggiungi il file .env al repo e usa .NET")
        self.invariato("Chiama la funzione main() e poi init( ).")
        self.invariato("Ciao :) come va")

    def test_codice_indentato_e_hashtag(self):
        self.invariato("Esempio:\n\n    al_fine_di()\n    pertanto = 1\n")
        self.invariato("Seguite #tuttavia e #pertanto")

    def test_titolo_markdown(self):
        self.assertEqual(pulisci("## È importante sottolineare che i test passano"), "## I test passano")
        self.invariato("# In conclusione")

    def test_marchi(self):
        self.assertEqual(pulisci("È importante notare che eBay chiude."), "eBay chiude.")

    def test_lineette(self):
        self.invariato("Il treno Roma–Milano parte alle 8.")
        self.invariato("— A casa — rispose lei — perché è tardi.")

    def test_solo_invisibili_non_rifinisce(self):
        t = "Ciao  mondo ,  come va ?"
        self.assertEqual(H.umanizza(t, DATI, passate=("invisibili",)).testo, t)

    def test_ripetizioni_volute(self):
        self.invariato("canta la la la tutto il giorno")

    def test_maiuscolo(self):
        self.invariato("AL FINE DI PROCEDERE VI INFORMIAMO")

    def test_riga_svuotata_rimossa(self):
        self.assertEqual(pulisci("Ciao!\n\nIn conclusione, ecco.\n\nFine."), "Ciao!\n\nEcco.\n\nFine.")

    def test_confini_di_parola(self):
        nomi = lambda t: [c.voce.voce for c in L.trova_lessico(t, DATI["voci"])]  # noqa: E731
        self.assertEqual(nomi("la robustezza del ponte"), [])
        self.assertTrue(nomi("un'esperienza unica"))
        self.assertTrue(nomi("le scelte strategiche"))

    def test_elenchi_enormi_in_tempo_lineare(self):
        import time
        t = ", ".join(["una due tre"] * 4000) + " e fine."
        t0 = time.time()
        detect.analizza(t, DATI)
        self.assertLess(time.time() - t0, 5)


class TestTell(unittest.TestCase):
    def ids(self, t):
        return {x.id for x in L.trova_tell(t)}

    def test_non_solo(self):
        self.assertIn("non-solo-ma", self.ids("Non è solo uno strumento, è un modo di lavorare."))

    def test_non_si_tratta_conta_una_volta(self):
        tt = L.trova_tell("Non si tratta di sostituire le persone, ma di liberarle.")
        self.assertEqual([x.id for x in tt if x.id in ("non-si-tratta", "non-ma")], ["non-si-tratta"])

    def test_titolo_maiuscolo(self):
        self.assertIn("titolo-maiuscolo", self.ids("## Come Usare L'Intelligenza Artificiale Nel Lavoro\n\nTesto."))

    def test_titolo_normale_non_segnalato(self):
        self.assertNotIn("titolo-maiuscolo", self.ids("## Come usare l'intelligenza artificiale nel lavoro\n\nTesto."))

    def test_chiusa_che_chiede_commenti(self):
        self.assertIn("chiusa-domanda", self.ids("Ho finito il refactoring.\n\nE voi come lo fate? Ditemi nei commenti."))

    def test_hashtag_per_riga(self):
        self.assertIn("muro-hashtag", self.ids("Post.\n#a #b #c #d #e #f"))
        self.assertNotIn("muro-hashtag", self.ids("#a #b #c\n#d #e #f"))

    def test_elenco_ordinale(self):
        self.assertIn("elenco-ordinale", self.ids("Primo: il tempo.\n\nSecondo: i soldi."))

    def test_testo_pulito_senza_tell(self):
        t = "Ieri ho spostato il database su un DGX Spark. Ci ho messo tre ore, due delle quali a capire un errore di permessi."
        self.assertEqual(self.ids(t), set())


class TestDetect(unittest.TestCase):
    def test_peggiore_segnalato(self):
        t = (RADICE / "bench" / "esempi" / "peggiore.txt").read_text(encoding="utf-8")
        self.assertEqual(detect.analizza(t, DATI).verdetto, "SEGNALATO")

    def test_riscritto_molto_meglio(self):
        prima = detect.analizza((RADICE / "bench" / "esempi" / "peggiore.txt").read_text(encoding="utf-8"), DATI)
        dopo = detect.analizza((RADICE / "bench" / "esempi" / "riscritto.txt").read_text(encoding="utf-8"), DATI)
        self.assertNotEqual(dopo.verdetto, "SEGNALATO")
        self.assertGreater(dopo.punteggio - prima.punteggio, 50)

    def test_abbreviazioni_non_toccate(self):
        t = "La Gold Hotel s.p.a., costituita poco prima, nonché la sede."
        self.assertEqual(pulisci(t), "La Gold Hotel s.p.a., costituita poco prima, e la sede.")

    def test_vuoto_e_non_italiano(self):
        self.assertEqual(detect.analizza("", DATI).verdetto, "N/D")
        en = "This is not just a tool, it is a revolution. Let me know in the comments what you think about it today."
        self.assertEqual(detect.analizza(en, DATI).verdetto, "N/D")

    def test_invisibili_limitano_il_punteggio(self):
        t = (RADICE / "bench" / "esempi" / "riscritto.txt").read_text(encoding="utf-8")
        r = detect.analizza(t.replace(" ", " ​", 3), DATI)
        self.assertLessEqual(r.punteggio, 60.0)
        self.assertTrue(r.ostacoli)

    def test_impronta_ignora_spazio_dopo_p_e_pp(self):
        c, _ = detect.c_impronta("Vedi p.\u00a08 e pp.\u00a018-19.", DATI["invisibili"])
        self.assertEqual(c.punteggio, 100.0)
        c, _ = detect.c_impronta("Vedi il\u00a0resto.", DATI["invisibili"])
        self.assertLess(c.punteggio, 100.0)

    def test_punteggi_nei_limiti(self):
        for t in ["", "ciao", "Ok.", "#a #b", "1 2 3 4 5"]:
            r = detect.analizza(t, DATI)
            self.assertGreaterEqual(r.punteggio, 0)
            self.assertLessEqual(r.punteggio, 100)

    def test_cli_codice_di_uscita(self):
        peggiore = str(RADICE / "bench" / "esempi" / "peggiore.txt")
        riscritto = str(RADICE / "bench" / "esempi" / "riscritto.txt")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(detect.main([peggiore, "--json", "--generico"]), 1)
            self.assertEqual(detect.main([riscritto, "--json", "--generico"]), 0)


class TestFrasi(unittest.TestCase):
    def test_abbreviazioni(self):
        self.assertEqual(len(L.frasi("Vedi art. 5 e pag. 3. Poi il resto.")), 2)

    def test_elenchi_a_capo(self):
        self.assertEqual(len(L.frasi("Lista:\n- uno\n- due")), 3)


if __name__ == "__main__":
    unittest.main()
