"""Comptage des syllabes par ligne.

- Français : hybride pyphen (lang='fr_FR') + comptage des noyaux vocaliques
  avec gestion du « e » muet, des élisions et des nasales. Pyphen seul
  sous-compte les petits mots (« alors » -> 1 au lieu de 2) à cause de ses
  règles leftmin/rightmin ; le comptage de noyaux rattrape ça.
  C'est une bonne approximation. Pour de la phonétique exacte : phonemizer
  + espeak (optionnel, voir README).
- Anglais : dictionnaire CMU via `pronouncing` (précis), fallback pyphen
  (patterns de césure, moins fiables : « banana » -> 2 au lieu de 3).
"""

from __future__ import annotations

import re
import statistics
from typing import List, Optional, Tuple

import pyphen

try:
    import pronouncing

    _HAS_PRONOUNCING = True
except ImportError:  # fallback pyphen si pronouncing n'est pas installé
    _HAS_PRONOUNCING = False

# Cache des dictionnaires pyphen (un par langue).
_DICS = {}

# « e » final prononcé (schwa) dans ces petits mots grammaticaux.
_E_FINAL_PRONONCE = {
    "le", "je", "te", "se", "ce", "me", "ne", "de", "que",
    "les", "des", "mes", "tes", "ses", "ces", "et", "es",
}

# Groupes de voyelles comptant pour UN noyau (diphtongues / hiatus traités
# par le regex de voyelles adjacentes, sauf pièges listés ici).
_VOYELLES = "aeiouyàâäéèêëîïôöùûüœ"
_NOYAU_RE = re.compile(f"[{_VOYELLES}]+")
# « ier », « ière », « ia », « io », « ua » = /jɛ/, /ja/, /jo/, /wa/ -> 1 noyau.
_GLISSANTE_RE = re.compile(r"(i[èe]|ia|io|ua|ue|ui)")


def get_dic(lang: str) -> pyphen.Pyphen:
    lang = {
        "en": "en_US", "eng": "en_US", "english": "en_US",
        "fr": "fr_FR", "fra": "fr_FR", "french": "fr_FR",
    }.get(lang.lower(), lang.lower())
    if lang not in _DICS:
        _DICS[lang] = pyphen.Pyphen(lang=lang)
    return _DICS[lang]


def _pyphen_count(word: str, lang: str) -> int:
    hyphenated = get_dic(lang).inserted(word)
    return max(1, len(hyphenated.split("-")))


def _noyaux_fr(word: str) -> int:
    """Approximation du nombre de syllabes françaises par comptage des
    noyaux vocaliques, avec gestion du « e » muet final."""
    m = word.lower()
    if m in _E_FINAL_PRONONCE:
        return 1
    # Terminaisons muettes : "ent" (3e pers. plur.), "es", "e" final.
    if m.endswith("ent") and len(m) > 3:
        m = m[:-2]  # "parlent" -> "parl"  (le « e » de « ent » est muet)
    elif m.endswith("es") and len(m) > 2 and m not in _E_FINAL_PRONONCE:
        m = m[:-1]  # "parles" -> "parle" puis e muet ci-dessous
    if m.endswith("e") and len(m) > 2 and m not in _E_FINAL_PRONONCE:
        m = m[:-1]  # « e » muet final
    if not m:
        return 1
    # Normalise les glissées pour ne pas compter « i » + voyelle comme 2 noyaux.
    m = _GLISSANTE_RE.sub("\x00", m)
    noyaux = _NOYAU_RE.findall(m)
    return max(1, len(noyaux))


def _cmu_count(word: str) -> Optional[int]:
    """Nombre de syllabes via le dictionnaire CMU (pronouncing).
    Retourne None si le mot est inconnu du dictionnaire."""
    if not _HAS_PRONOUNCING:
        return None
    phones_list = pronouncing.phones_for_word(word.lower())
    if not phones_list:
        return None
    # Chaque syllabe = un phone portant un indice de stress (0, 1 ou 2).
    return sum(1 for ph in phones_list[0].split() if any(c.isdigit() for c in ph))


def count_syllables_word(word: str, lang: str) -> int:
    """Nombre de syllabes d'un mot (>= 1 pour un mot non vide)."""
    word = word.strip()
    if not word:
        return 0
    # On retire la ponctuation collée au mot (apostrophes et tirets séparés
    # sont traités comme des séparateurs de mots par l'appelant).
    word = re.sub(r"[^\w'’-]", "", word, flags=re.UNICODE)
    if not word:
        return 0

    lang = lang.lower()
    if lang in ("fr", "fra", "french"):
        return max(_pyphen_count(word, "fr"), _noyaux_fr(word))
    # anglais (et autres langues latines supportées par pyphen)
    cmu = _cmu_count(word) if lang in ("en", "eng", "english") else None
    if cmu is not None:
        return cmu
    return _pyphen_count(word, "en" if lang in ("en", "eng", "english") else lang)


def count_syllables_line(line: str, lang: str) -> int:
    """Nombre de syllabes d'une ligne de paroles.

    Les apostrophes/tirets sont des séparateurs : « l'amour » compte comme
    « l » + « amour », « peut-être » comme « peut » + « être ».
    """
    line = re.sub(r"['’\-]", " ", line)
    return sum(count_syllables_word(w, lang) for w in line.split())


def syllables_per_line(plain_lyrics: str, lang: str) -> List[int]:
    """Liste des comptages de syllabes, une entrée par ligne non vide."""
    lines = [l.strip() for l in plain_lyrics.splitlines() if l.strip()]
    return [count_syllables_line(l, lang) for l in lines]


# ---------------------------------------------------------------------------
# Paroles synchronisées (format LRC) -> débit en syllabes/seconde
# ---------------------------------------------------------------------------

_LRC_RE = re.compile(r"\[(\d+):(\d+(?:[.,]\d+)?)\]")


def parse_lrc(synced_lyrics: str) -> List[Tuple[float, str]]:
    """Parse du LRC : retourne [(timestamp_en_secondes, texte), ...]."""
    out = []
    for raw in synced_lyrics.splitlines():
        matches = _LRC_RE.findall(raw)
        if not matches:
            continue
        text = _LRC_RE.sub("", raw).strip()
        if not text:
            continue
        # Une ligne LRC peut avoir plusieurs timestamps ; on prend le premier.
        mm, ss = matches[0]
        out.append((int(mm) * 60 + float(ss.replace(",", ".")), text))
    return out


def speech_rate(
    syllable_counts: List[int],
    synced_lyrics: Optional[str],
    duration_seconds: Optional[float],
) -> Optional[float]:
    """Débit en syllabes/seconde.

    durée = durée officielle du morceau (LRCLIB) si connue, sinon le timestamp
    de la dernière ligne synchronisée.
    """
    total = sum(syllable_counts)
    if total <= 0:
        return None
    duree = duration_seconds
    if duree is None and synced_lyrics:
        parsed = parse_lrc(synced_lyrics)
        if parsed:
            duree = parsed[-1][0]
    if not duree or duree <= 0:
        return None
    return round(total / duree, 3)


# ---------------------------------------------------------------------------
# Statistiques du morceau
# ---------------------------------------------------------------------------

def stats(counts: List[int]) -> dict:
    """Colonnes calculées à partir de la liste des syllabes par ligne."""
    if not counts:
        return {
            "nb_lignes": 0,
            "total_syllabes": 0,
            "moy_syllabes_par_ligne": None,
            "ecart_type_syllabes": None,
        }
    return {
        "nb_lignes": len(counts),
        "total_syllabes": sum(counts),
        "moy_syllabes_par_ligne": round(statistics.fmean(counts), 2),
        "ecart_type_syllabes": round(statistics.pstdev(counts), 2) if len(counts) > 1 else 0.0,
    }
