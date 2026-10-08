"""Tests hors-ligne (aucun appel réseau) : comptage de syllabes, stats, LRC,
détection de langue et construction d'une ligne de dataset à partir de paroles
injectées à la main (elles-ci sont des phrases de test, pas des paroles protégées).

Lancer depuis data/ :  python -m unittest discover -s tests -v
(ou : .venv/bin/python -m unittest discover -s tests -v)
"""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipeline.langdetect import detect_language
from pipeline.lyrics import LyricsResult
from pipeline.pipeline import row_from_lyrics
from pipeline.streams import normalize_key, parse_streams_value
from pipeline.syllables import (
    count_syllables_line,
    parse_lrc,
    speech_rate,
    stats,
    syllables_per_line,
)


class TestSyllablesFr(unittest.TestCase):
    def test_ligne_simple(self):
        # « Alors on danse » -> A-lors (2) + on (1) + danse (1)
        self.assertEqual(count_syllables_line("Alors on danse", "fr"), 4)

    def test_e_muet(self):
        # « le » compte 1 syllabe malgré le e muet
        self.assertEqual(count_syllables_line("le chat", "fr"), 2)

    def test_ligne_vide(self):
        self.assertEqual(count_syllables_line("   ", "fr"), 0)

    def test_syllables_per_line_ignore_lignes_vides(self):
        paroles = "Un deux\n\nTrois quatre cinq\n"
        self.assertEqual(syllables_per_line(paroles, "fr"), [2, 3])


class TestSyllablesEn(unittest.TestCase):
    def test_ligne_simple(self):
        # « Hello world » -> hel-lo (2) + world (1)
        self.assertEqual(count_syllables_line("Hello world", "en"), 3)

    def test_mot_compose(self):
        # « banana » -> ba-na-na (3)
        self.assertEqual(count_syllables_line("banana", "en"), 3)


class TestStats(unittest.TestCase):
    def test_stats_base(self):
        s = stats([5, 6, 4, 7])
        self.assertEqual(s["nb_lignes"], 4)
        self.assertEqual(s["total_syllabes"], 22)
        self.assertAlmostEqual(s["moy_syllabes_par_ligne"], 5.5)
        self.assertGreater(s["ecart_type_syllabes"], 0)

    def test_stats_une_ligne(self):
        s = stats([5])
        self.assertEqual(s["ecart_type_syllabes"], 0.0)

    def test_stats_vide(self):
        s = stats([])
        self.assertEqual(s["nb_lignes"], 0)
        self.assertIsNone(s["moy_syllabes_par_ligne"])


class TestLrc(unittest.TestCase):
    def test_parse_lrc(self):
        lrc = "[00:12.50]Première ligne\n[01:05.00]Deuxième ligne\n"
        parsed = parse_lrc(lrc)
        self.assertEqual(len(parsed), 2)
        self.assertAlmostEqual(parsed[0][0], 12.5)
        self.assertEqual(parsed[0][1], "Première ligne")
        self.assertAlmostEqual(parsed[1][0], 65.0)

    def test_speech_rate_avec_duree(self):
        # 12 syllabes sur 200 secondes -> 0.06 syll/s
        self.assertAlmostEqual(speech_rate([5, 7], None, 200.0), 0.06)

    def test_speech_rate_sans_duree(self):
        rate = speech_rate([4, 4], "[00:10.00]aaaa\n[00:20.00]bbbb\n", None)
        self.assertAlmostEqual(rate, 8 / 20.0)

    def test_speech_rate_sans_donnees(self):
        self.assertIsNone(speech_rate([], None, None))


class TestLangDetect(unittest.TestCase):
    def test_fr(self):
        self.assertEqual(detect_language("Je ne sais pas quoi faire avec toi ce soir"), "fr")

    def test_en(self):
        self.assertEqual(detect_language("I don't know what to do with you tonight"), "en")

    def test_defaut_si_aucun_mot_outil(self):
        # « zip » / « zim » ne sont dans aucune liste de mots-outils
        self.assertEqual(detect_language("zip zim zum", default="en"), "en")


class TestStreamsHelpers(unittest.TestCase):
    def test_normalize_key(self):
        self.assertEqual(
            normalize_key("Stromae", "Alors on danse !"),
            normalize_key("stromae", "Alors on Danse"),
        )
        # accents ignorés
        self.assertEqual(normalize_key("Angèle", "Djadja"), normalize_key("Angele", "Djadja"))

    def test_parse_streams(self):
        self.assertEqual(parse_streams_value("1,234,567"), 1234567)
        self.assertEqual(parse_streams_value("1 234 567"), 1234567)
        self.assertEqual(parse_streams_value(1234567), 1234567)
        self.assertIsNone(parse_streams_value(""))
        self.assertIsNone(parse_streams_value(None))


class TestRowFromLyrics(unittest.TestCase):
    """Construction d'une ligne de dataset sans réseau (paroles injectées)."""

    PAROLES_TEST = "Quand lerektro s'allume\nTout le monde danse"  # fictif

    def _lyrics(self):
        return LyricsResult(
            artist_name="Artiste Test",
            track_name="Titre Test",
            album_name="",
            duration=200.0,
            plain_lyrics=self.PAROLES_TEST,
            synced_lyrics="[00:10.00]Quand lerektro s'allume\n[00:20.00]Tout le monde danse\n",
            instrumental=False,
        )

    def test_row_complete(self):
        song = {"artiste": "Artiste Test", "titre": "Titre Test", "langue": None}
        streams_index = {normalize_key("Artiste Test", "Titre Test"): {"streams": 1234567}}
        row = row_from_lyrics(song, self._lyrics(), "auto", streams_index)

        self.assertTrue(row["paroles_trouvees"])
        self.assertTrue(row["paroles_synchonisees"])
        self.assertEqual(row["streams"], 1234567)
        self.assertEqual(row["langue"], "fr")
        counts = json.loads(row["syllabes_par_ligne"])
        self.assertEqual(len(counts), 2)
        self.assertEqual(row["nb_lignes"], 2)
        self.assertEqual(row["total_syllabes"], sum(counts))
        self.assertIsNotNone(row["debit_syllabes_par_seconde"])
        # Le dataset ne doit contenir AUCUN texte de paroles
        for col in ("syllabes_par_ligne",):
            self.assertNotIn("danse", row[col])

    def test_row_sans_paroles(self):
        song = {"artiste": "Inconnu", "titre": "Rien", "langue": None}
        row = row_from_lyrics(song, None, "auto", {})
        self.assertFalse(row["paroles_trouvees"])
        self.assertIsNone(row["syllabes_par_ligne"])
        self.assertEqual(row["nb_lignes"], 0)

    def test_row_instrumental(self):
        song = {"artiste": "Inconnu", "titre": "Rien", "langue": None}
        row = row_from_lyrics(song, LyricsResult(instrumental=True, plain_lyrics=""), "auto", {})
        self.assertFalse(row["paroles_trouvees"])


if __name__ == "__main__":
    unittest.main()
