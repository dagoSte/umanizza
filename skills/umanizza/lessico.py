"""Nucleo condiviso di umanizza: carica slop.json e trova lessico e tell.

Solo libreria standard. Nessuna rete. Importato da humanize.py e detect.py.
"""
from __future__ import annotations

import difflib
import json
import re
import statistics
import unicodedata
from dataclasses import dataclass
from pathlib import Path

QUI = Path(__file__).resolve().parent
LESSICO_PREDEFINITO = QUI / "slop.json"

# --------------------------------------------------------------------------
# Caricamento
# --------------------------------------------------------------------------


@dataclass
class Voce:
    voce: str
    cat: str
    sostituisci: str | None
    peso: float
    perche: str
    nota: str
    rx: re.Pattern
    conta: bool = True  # False: segnalata e sostituita come sempre, ma non conta nel controllo SLOP

    @property
    def solo_segnala(self) -> bool:
        return self.sostituisci is None


def _compila(v: str, is_regex: bool) -> re.Pattern:
    corpo = v if is_regex else re.escape(v)
    # Confine a sinistra: niente lettera prima (l'apostrofo va bene: "un'esperienza").
    sx = r"(?<!\w)" if re.match(r"[\w(\[]", v) else ""
    # Confine a destra sempre, tranne quando la voce finisce con punteggiatura letterale.
    dx = "" if re.search(r"[:;,!?]$|\\\?$|[^\w\s\])+?*}]$", v) else r"(?!\w)"
    return re.compile(sx + "(?:" + corpo + ")" + dx, re.IGNORECASE)


def carica(path: str | Path | None = None) -> dict:
    p = Path(path) if path else LESSICO_PREDEFINITO
    dati = json.loads(p.read_text(encoding="utf-8"))
    voci = []
    for e in dati["lessico"]:
        voci.append(
            Voce(
                voce=e["voce"],
                cat=e.get("cat", ""),
                sostituisci=e.get("sostituisci"),
                peso=float(e.get("peso", 1.0)),
                perche=e.get("perche", ""),
                nota=e.get("nota", ""),
                rx=_compila(e["voce"], bool(e.get("regex"))),
                conta=bool(e.get("slop", True)),
            )
        )
    invis = {}
    for e in dati["invisibili"]:
        codici = []
        if "codici" in e:
            codici = [int(c, 16) for c in e["codici"]]
        if "intervallo" in e:
            a, b = (int(c, 16) for c in e["intervallo"])
            codici = list(range(a, b + 1))
        for c in codici:
            invis[c] = (e["nome"], e["sostituisci"])
    return {"voci": voci, "invisibili": invis, "tell": {t["id"]: t for t in dati["tell"]}, "domande": dati.get("domande", {})}


# --------------------------------------------------------------------------
# Zone protette: codice, URL, email, menzioni. Il lessico non le tocca.
# --------------------------------------------------------------------------

_RX_PROTETTE = re.compile(
    r"```.*?(?:```|\Z)"  # blocchi di codice
    r"|`[^`\n]+`"  # codice inline
    r"|https?://\S+|www\.\S+"  # URL
    r"|[\w.+-]+@[\w-]+\.[\w.]+"  # email
    r"|(?<!\w)@\w+"  # menzioni
    r"|(?<![\w&])#[\wÀ-ÿ]+"  # hashtag (non i titoli markdown, che hanno lo spazio)
    r"|(?m:^(?: {4}|\t)[^\n]*$)",  # codice indentato
    re.DOTALL,
)


def zone_protette(testo: str) -> list[tuple[int, int]]:
    return [m.span() for m in _RX_PROTETTE.finditer(testo)]


def _in_zona(pos: tuple[int, int], zone: list[tuple[int, int]]) -> bool:
    a, b = pos
    return any(a < zb and b > za for za, zb in zone)


# --------------------------------------------------------------------------
# Apparato di una tesi (modalità accademica): citazioni autore-anno, rimandi di pagina, richiami di nota.
# Dice chi è stato citato, non chi ha scritto la prosa intorno: in una tesi satura CONCRETEZZA per via del genere.
# --------------------------------------------------------------------------

_PAG = r"pp?\.\s?\d+(?:\s?[-–]\s?\d+)?"
# Parole maiuscole che aprono una data, non una citazione: «Nel 1929», «Nell'aprile 1977», «Dal 1984».
_NON_AUTORI = (
    r"Nel|Nell|Nella|Nelle|Negli|Dal|Dall|Dalla|Dalle|Dagli|Al|All|Alla|Il|Lo|La|Le|Gli|I|Del|Della|Sul|Sulla|"
    r"In|A|Da|Di|Per|Con|Su|Tra|Fra|Fino|Sino|Sin|Dopo|Prima|Entro|Verso|Intorno|Durante|Oltre|Circa|Già|Solo|"
    r"Ancora|Anche|Proprio|Mentre|Quando|Ecco|E|Ma|Ed|Gennaio|Febbraio|Marzo|Aprile|Maggio|Giugno|Luglio|Agosto|"
    r"Settembre|Ottobre|Novembre|Dicembre"
)
_RX_APPARATO = re.compile(
    r"\[\^\d+\]|[⁰¹²³⁴⁵⁶⁷⁸⁹]+"  # richiami di nota
    rf"|(?:\b[A-Z]{{2,6}}|\bcit\.|\bibid(?:em)?\.?|\bivi)\s*,?\s*{_PAG}"  # «MM, p. 8», «cit., pp. 3-4»
    rf"|\b(?!(?:{_NON_AUTORI})\b)[A-ZÀ-Ý][\w'’-]+(?:\s+(?:et al\.|e|and|&)(?:\s+[A-ZÀ-Ý][\w'’-]+)?)?,?\s+"
    rf"\(?(?:1[5-9]|20)\d\d[a-z]?\)?(?:\s*,\s*{_PAG})?"  # «Rossi, 2019», «Rossi (2019)», «Neri et al., 2017, p. 3»
    rf"|\b{_PAG}"  # «p. 8» da solo
)


def togli_apparato(testo: str) -> str:
    """Il testo senza citazioni autore-anno, rimandi di pagina e richiami di nota."""
    return _RX_APPARATO.sub("", testo)


# --------------------------------------------------------------------------
# Emoji (per non rompere sequenze ZWJ e bandiere)
# --------------------------------------------------------------------------


def is_emoji(ch: str) -> bool:
    if not ch:
        return False
    o = ord(ch)
    return (
        0x1F000 <= o <= 0x1FAFF
        or 0x2600 <= o <= 0x27BF
        or 0x2B00 <= o <= 0x2BFF
        or 0x2300 <= o <= 0x23FF
        or o in (0x00A9, 0x00AE, 0x203C, 0x2049, 0x2122, 0x2139, 0x3030, 0x303D)
    )


def _emoji_vicino(testo: str, i: int, direzione: int) -> bool:
    """C'è un'emoji subito prima/dopo i (saltando selettori e toni di pelle)?"""
    j = i + direzione
    while 0 <= j < len(testo) and (ord(testo[j]) in (0xFE0F, 0xFE0E) or 0x1F3FB <= ord(testo[j]) <= 0x1F3FF):
        j += direzione
    return 0 <= j < len(testo) and is_emoji(testo[j])


# «p. 8», «pp. 8-9»: lo spazio indivisibile dopo l'abbreviazione è tipografia voluta.
_PAGINA = re.compile(r"(?:^|\W)pp?\.$")


def invisibili(testo: str, tabella: dict) -> list[tuple[int, str, str]]:
    """Restituisce (posizione, nome, sostituzione) per ogni carattere da togliere.

    Rispetta le sequenze emoji: ZWJ tra due emoji e i tag delle bandiere
    di suddivisione (🏴 + tag + U+E007F) restano. Resta anche lo spazio
    indivisibile (U+00A0, U+202F) dopo «p.» e «pp.».
    """
    trovati = []
    in_bandiera = False
    for i, ch in enumerate(testo):
        o = ord(ch)
        is_tag = 0xE0020 <= o <= 0xE007F
        if o == 0x1F3F4:
            in_bandiera = True
            continue
        if is_tag and in_bandiera:
            if o == 0xE007F:
                in_bandiera = False
            continue
        if not is_tag:
            in_bandiera = False
        if o not in tabella:
            continue
        if o == 0x200D and _emoji_vicino(testo, i, -1) and _emoji_vicino(testo, i, 1):
            continue
        if o in (0x00A0, 0x202F) and _PAGINA.search(testo[max(0, i - 4) : i]):
            continue
        nome, sost = tabella[o]
        trovati.append((i, nome, sost))
    return trovati


# --------------------------------------------------------------------------
# Lessico
# --------------------------------------------------------------------------


@dataclass
class Colpo:
    inizio: int
    fine: int
    testo: str
    voce: Voce


def trova_lessico(testo: str, voci: list[Voce]) -> list[Colpo]:
    zone = zone_protette(testo)
    colpi: list[Colpo] = []
    occupato: list[tuple[int, int]] = []
    for v in voci:
        for m in v.rx.finditer(testo):
            if m.end() == m.start() or _in_zona(m.span(), zone):
                continue
            # Una sovrapposizione con una voce già trovata non conta doppio
            # (es. "gioca un ruolo chiave" e "gioca un ruolo").
            if _in_zona(m.span(), occupato):
                continue
            colpi.append(Colpo(m.start(), m.end(), m.group(0), v))
            occupato.append(m.span())
    colpi.sort(key=lambda c: c.inizio)
    return colpi


# --------------------------------------------------------------------------
# Frasi e parole
# --------------------------------------------------------------------------

_ABBR = r"(?:es|ecc|etc|sig|sigg|dott|dr|prof|ing|avv|art|artt|pag|pagg|n|nn|cap|vol|cfr|vs|ca|p|pp|st|sec|min|tel|fig)"
_RX_FRASE = re.compile(
    r"(?<=[.!?…])[\"'»”)\]]*\s+(?=[\"'«“(\[]*[A-ZÀ-ÖØ-Ý0-9@#*\-•])|\n+"
)
_RX_PAROLA = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+(?:['’][A-Za-zÀ-ÖØ-öø-ÿ]+)*")


def _togli_codice(testo: str) -> str:
    return re.sub(r"```.*?(?:```|\Z)", " ", testo, flags=re.DOTALL)


def frasi(testo: str) -> list[str]:
    testo = _togli_codice(testo)
    # Proteggi le abbreviazioni dal taglio.
    segnaposto = re.sub(r"\b(" + _ABBR + r")\.(?=\s)", lambda m: m.group(1) + "\u0000", testo, flags=re.I)
    pezzi = [p.replace("\u0000", ".").strip() for p in _RX_FRASE.split(segnaposto)]
    return [p for p in pezzi if p and parole(p)]


def parole(testo: str) -> list[str]:
    return _RX_PAROLA.findall(testo)


# --------------------------------------------------------------------------
# Tell strutturali
# --------------------------------------------------------------------------

_PIC = "\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿"
_RX_RIGA_EMOJI = re.compile(rf"^\s*[{_PIC}]")
_RX_FINE_EMOJI = re.compile(rf"[{_PIC}]️?\s*$")

_TELL_RX = {
    "non-solo-ma": re.compile(
        r"\bnon (?:è|e'|sono|era|erano|sarà|serve|basta) (?:più )?(?:solo|soltanto|semplicemente|soltanto|un semplice|una semplice)\b"
        r"[^.!?\n]{1,90}?(?:[,;:.—–-]\s*|\s+)(?:ma\b|è\b|sono\b|bensì\b)",
        re.I,
    ),
    "non-si-tratta": re.compile(
        r"\bnon si tratta (?:solo |soltanto |semplicemente )?di\b[^.!?\n]{1,90}?(?:[,;.—–-]\s*)(?:ma|bensì|si tratta)\b",
        re.I,
    ),
    "domanda-risposta": re.compile(
        r"(?:^|(?<=[.!\n])\s*)((?:il|la|lo|i|le|gli|l'|e|ma|perché|come|cosa|risultato|motivo|morale|problema|soluzione|segreto|verità)"
        r"[^?.!\n]{0,28}\?)[ \t]+[A-ZÀ-Ú\w]",
        re.I | re.M,
    ),
    "rivelazione-due-punti": re.compile(
        r"\b(?:la verità|il punto|il segreto|il motivo|la risposta|il problema|la differenza|la lezione|la chiave|la morale|il trucco)"
        r"(?: (?:è|sta|era) (?:una|uno|semplice|questa|questo|qui|tutta qui|semplicissima))?\s*[:?]",
        re.I,
    ),
    "non-ma": re.compile(r"\bnon\b[^.!?\n:]{2,70}, ma\b", re.I),
    "non-due-punti": re.compile(r"\bnon (?:serve|conta|basta|è|sono|si tratta)\b[^.!?\n:]{1,60}: \S", re.I),
    "concessione": re.compile(r"\b(?:sembra|può sembrare|potrebbe sembrare|sembrerà)\b[^.!?\n]{0,40}, ma\b", re.I),
    "piu-piu": re.compile(r"\b(?:più|meno)\b[^,.!?\n]{1,40}, (?:più|meno)\b", re.I),
    "ordinale": re.compile(
        r"(?m)^[ \t]*[*_#>\-]*[ \t]*(?:primo|secondo|terzo|quarto|quinto|il primo|il secondo|il terzo|il quarto|la prima|la seconda|la terza|"
        r"in primo luogo|in secondo luogo|prima di tutto|errore \d|consiglio \d|step \d|passo \d|[1-9]️⃣)\b",
        re.I,
    ),
    "cta": re.compile(
        r"\b(?:nei commenti|qui sotto|fatemi sapere|fammi sapere|dimmelo|sono curios[oa] di|"
        r"condividilo|condividetelo|salvalo|salvatelo|seguimi|seguitemi)\b|\be (?:voi|tu)\s*\?",
        re.I,
    ),
    # Quantificatori limitati e senza annidamenti: tempo lineare anche su elenchi enormi.
    "triade": re.compile(r"[^,.;:!?\n]{1,40}, [^,.;:!?\n]{1,40} (?:e|o) [\wàèéìòù]", re.I),
    "grassetto-diffuso": re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__"),
    "hashtag": re.compile(r"(?<!\w)#[\wÀ-ÿ]+"),
}

_STOP_ANAFORA = {"il", "la", "lo", "i", "le", "gli", "un", "una", "uno", "e", "ma", "in", "di", "a", "l", "è", "non", "che", "per"}


def _titolo_maiuscolo(riga: str) -> bool:
    r = re.sub(r"^[#>*\-\s\d.)]+", "", riga.strip()).strip("*_ ")
    if not r or r.endswith((".", ",", ";")) or r.isupper():
        return False
    pp = parole(r)
    if not 3 <= len(pp) <= 14:
        return False
    lunghe = [p for p in pp[1:] if len(p) > 3]
    if len(lunghe) < 3:
        return False
    maiusc = [p for p in lunghe if p[0].isupper() and not p.isupper()]
    return len(maiusc) / len(lunghe) >= 0.75


@dataclass
class Tell:
    id: str
    riga: int
    estratto: str
    peso: float = 1.0


def _riga_di(testo: str, pos: int) -> int:
    return testo.count("\n", 0, pos) + 1


_RX_FATTO = re.compile(r"\d|(?<![\w'’])[A-ZÀ-Ý]")


def _ha_fatto(pp: list[str]) -> bool:
    return any(_RX_FATTO.match(p) or any(c.isdigit() for c in p) for p in pp)


def _triade_fattuale(testo: str, m: re.Match) -> bool:
    """Elenco in cui ogni elemento ha un nome proprio, una cifra o un anno («Madrid, Barcellona e Burgos»)."""
    primo, resto = m.group(0).split(", ", 1)
    medio = re.sub(r"\s+(?:e|o)$", "", resto[:-1].rstrip(), flags=re.I)
    ultimo = re.match(r"[^,.;:!?\n)]{1,40}", testo[m.end() - 1:])
    pp = parole(primo)
    prima = testo[: m.start()]
    if not prima.strip() or re.search(r"[.!?\n]\s*$", prima):
        pp = pp[1:]  # la prima parola della frase è maiuscola per posizione, non perché è un nome
    return _ha_fatto(pp[-3:]) and _ha_fatto(parole(medio)) and bool(ultimo) and _ha_fatto(parole(ultimo.group(0)))


def trova_tell(testo: str, accademico: bool = False) -> list[Tell]:
    pulito = _togli_codice(testo)
    trovati: list[Tell] = []
    n_parole = max(1, len(parole(pulito)))

    occupati: list[tuple[int, int]] = []

    def _da_rx(tid: str, peso: float = 1.0):
        for m in _TELL_RX[tid].finditer(pulito):
            if _in_zona(m.span(), occupati):
                continue  # "Non si tratta di X, ma di Y" conta una volta sola
            occupati.append(m.span())
            trovati.append(Tell(tid, _riga_di(pulito, m.start()), m.group(0)[:80], peso))

    _da_rx("non-solo-ma")
    _da_rx("non-si-tratta")
    _da_rx("rivelazione-due-punti")
    _da_rx("non-ma", 0.6)
    _da_rx("non-due-punti")
    _da_rx("concessione")
    _da_rx("piu-piu")
    ordinali = list(_TELL_RX["ordinale"].finditer(pulito))
    if len(ordinali) >= 2:
        for m in ordinali:
            trovati.append(Tell("elenco-ordinale", _riga_di(pulito, m.start()), m.group(0).strip()[:80], 0.6))
    # Domanda e risposta: solo domande brevi (max 5 parole).
    for m in _TELL_RX["domanda-risposta"].finditer(pulito):
        q = m.group(1)
        if len(parole(q)) <= 5 and not re.search(r"\b(tu|voi|ti|vi|te)\b", q, re.I):
            trovati.append(Tell("domanda-risposta", _riga_di(pulito, m.start()), q[:80], 0.3))

    # Triadi ed elenchi in linea: uno è normale, la raffica no. Il primo è gratis,
    # ogni altro pesa poco ma si somma (nei testi IA misurati: ~3.5x la densità umana).
    triadi = [m for m in _TELL_RX["triade"].finditer(pulito) if not _in_zona(m.span(), occupati)]
    if accademico:  # in una tesi un elenco di nomi, opere e date è un fatto da conservare, non un ritmo
        triadi = [m for m in triadi if not _triade_fattuale(pulito, m)]
    for m in triadi[1:]:
        trovati.append(Tell("triade", _riga_di(pulito, m.start()), m.group(0)[:80], 0.35))

    righe = pulito.split("\n")
    piene = [r for r in righe if r.strip()]

    con_emoji = [i for i, r in enumerate(righe) if _RX_RIGA_EMOJI.match(r)]
    if len(con_emoji) >= 2:
        for i in con_emoji:
            trovati.append(Tell("elenco-emoji", i + 1, righe[i].strip()[:80], 0.7))

    for i, r in enumerate(righe):
        if _titolo_maiuscolo(r):
            trovati.append(Tell("titolo-maiuscolo", i + 1, r.strip()[:80]))

    grassetti = list(_TELL_RX["grassetto-diffuso"].finditer(pulito))
    if len(grassetti) >= 3:
        for m in grassetti:
            trovati.append(Tell("grassetto-diffuso", _riga_di(pulito, m.start()), m.group(0)[:80], 0.4))

    for i, r in enumerate(righe):
        hashtag = _TELL_RX["hashtag"].findall(r)
        if len(hashtag) > 5:
            trovati.append(Tell("muro-hashtag", i + 1, f"{len(hashtag)} hashtag: " + " ".join(hashtag[:8]), 1.5))

    ff = frasi(pulito)
    ecco = [f for f in ff if re.match(r"[\W_]*ecco\b", f, re.I)]
    if len(ecco) >= 2:
        for f in ecco:
            trovati.append(Tell("apertura-ecco", 0, f[:80], 0.7))

    significative = [r for r in piene if not re.fullmatch(r"\s*(#[\wÀ-ÿ]+\s*)+", r)]
    coda = significative[-2:]
    for r in coda:
        u = r.strip()
        domanda_al_lettore = "?" in u and re.search(
            r"\b(tu|voi|ti|vi|te|tuo|tua|vostro|vostra|vostri|vostre|tuoi|tue|pensi|pensate|usate|usi|fate|fai)\b", u, re.I
        )
        if domanda_al_lettore or _TELL_RX["cta"].search(u):
            trovati.append(Tell("chiusa-domanda", len(righe), u[:80]))
            break

    lunghezze = [len(parole(f)) for f in ff]
    if len(lunghezze) >= 6:
        cv = statistics.pstdev(lunghezze) / max(1e-9, statistics.mean(lunghezze))
        if cv < 0.28:
            trovati.append(Tell("ritmo-uniforme", 0, f"variazione {cv:.2f} su {len(lunghezze)} frasi"))

    for i in range(len(ff) - 2):
        a = [p.lower() for p in parole(ff[i])[:2]]
        b = [p.lower() for p in parole(ff[i + 1])[:2]]
        c = [p.lower() for p in parole(ff[i + 2])[:2]]
        if a and a[0] not in _STOP_ANAFORA and a[0] == b[0] == c[0]:
            trovati.append(Tell("anafora", 0, f"tre frasi aprono con «{a[0]}»"))
            break
        if len(a) == len(b) == len(c) == 2 and a == b == c:
            trovati.append(Tell("anafora", 0, f"tre frasi aprono con «{' '.join(a)}»"))
            break

    fine_emoji = [r for r in piene if _RX_FINE_EMOJI.search(r)]
    if len(fine_emoji) >= 3 and len(fine_emoji) / len(piene) >= 0.5:
        trovati.append(Tell("emoji-fine-riga", 0, f"{len(fine_emoji)} righe su {len(piene)}", 0.7))

    return trovati


# --------------------------------------------------------------------------
# Impronta tipografica
# --------------------------------------------------------------------------


def lineette(testo: str) -> list[int]:
    """Lineette em/en usate come incisi (non quelle del dialogo a inizio riga)."""
    pos = []
    for m in re.finditer(r"[—–]", _togli_codice(testo)):
        i = m.start()
        inizio_riga = testo.rfind("\n", 0, i) + 1
        if testo[inizio_riga:i].strip() == "":
            continue  # dialogo o elenco
        if m.group(0) == "–" and i > 0 and testo[i - 1].isdigit() and i + 1 < len(testo) and testo[i + 1].isdigit():
            continue  # intervallo numerico 10–20
        pos.append(i)
    return pos


def normalizza_nfc(testo: str) -> str:
    return unicodedata.normalize("NFC", testo)


# --------------------------------------------------------------------------
# Fedeltà: i fatti che una riscrittura non deve perdere né inventare.
# Numeri, nomi propri (maiuscole a metà frase), virgolettati; più la quota di parole cambiate.
# --------------------------------------------------------------------------

_RX_NUMERO = re.compile(r"\d+")
_RX_VIRGOLETTATO = re.compile(r"«[^«»\n]{3,}»|“[^“”\n]{3,}”|\"[^\"\n]{3,}\"")
_MAIUSCOLE_COMUNI = {
    "Il", "Lo", "La", "I", "Gli", "Le", "Un", "Uno", "Una", "E", "Ed", "Ma", "O", "Non", "Che", "Se", "Per", "In", "A",
    "Da", "Di", "Con", "Su", "Tra", "Fra", "Nel", "Nella", "Nei", "Nelle", "Del", "Della", "Al", "Alla", "Io", "Tu",
    "Lei", "Lui", "Noi", "Voi", "Loro", "Ecco", "Sì", "No", "Ok",
}


def _nomi(testo: str) -> set[str]:
    out = set()
    for f in frasi(testo):
        for p in parole(f)[1:]:
            if p[:1].isupper() and p not in _MAIUSCOLE_COMUNI:
                out.add(p)
    return out


def confronta_fatti(prima: str, dopo: str) -> dict:
    """Fatti di «prima» spariti in «dopo», fatti comparsi solo in «dopo», quota di parole cambiate (0-1)."""
    prima, dopo = normalizza_nfc(prima), normalizza_nfc(dopo)
    parole_dopo, parole_prima = set(parole(dopo)), set(parole(prima))
    num_a, num_b = set(_RX_NUMERO.findall(prima)), set(_RX_NUMERO.findall(dopo))
    # apostrofi e virgolette curve o dritte contano uguale: la pulizia tipografica non fa sparire una citazione
    tipo = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "“": '"', "”": '"', "„": '"'})
    norm = lambda s: " ".join(s.translate(tipo).split())  # noqa: E731
    citazioni = [m.group(0) for m in _RX_VIRGOLETTATO.finditer(prima) if norm(m.group(0)[1:-1]) not in norm(dopo)]
    persi = sorted(num_a - num_b) + sorted(n for n in _nomi(prima) if n not in parole_dopo) + citazioni
    nuovi = sorted(num_b - num_a) + sorted(n for n in _nomi(dopo) if n not in parole_prima)
    cambiato = 1 - difflib.SequenceMatcher(None, parole(prima), parole(dopo), autojunk=False).ratio()
    return {"persi": persi, "nuovi": nuovi, "cambiato": round(cambiato, 3)}
