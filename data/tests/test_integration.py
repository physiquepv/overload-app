"""Test d'intégration hors-ligne : on mocke les appels HTTP (LRCLIB + Spotify
Charts) et on vérifie que le CLI produit bien le dataset final, avec les bonnes
colonnes et les bonnes valeurs calculées.

Lancer depuis data/ :  python -m unittest discover -s tests -v
"""

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from pipeline import streams as streams_mod
from pipeline.pipeline import load_songs_csv
from pipeline.streams import load_streams_csv
import run_pipeline

# Paroles de TEST (phrases inventées, pas de contenu protégé par le droit
# d'auteur) + fausses réponses d'API.
FAKE_LRCLIB_GET = {
    "artistName": "Artiste Test",
    "trackName": "Titre Test",
    "albumName": "Album Test",
    "duration": 200.0,
    "instrumental": False,
    "plainLyrics": "Quand la musique monte\nTout le monde danse fort",
    "syncedLyrics": "[00:10.00]Quand la musique monte\n[00:30.00]Tout le monde danse fort\n",
}
FAKE_CHART = {
    "entries": [
        {"rank": 1, "track_name": "Titre Test", "artist_name": "Artiste Test", "streams": 1234567},
        {"rank": 2, "track_name": "Autre Titre", "artist_name": "Quelqu'un", "streams": "987,654"},
    ]
}


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"{self.status_code}")


def fake_get(self, url, params=None, timeout=None, headers=None):
    if "/api/get" in url:
        if params and params.get("track_name") == "Titre Test":
            return FakeResponse(FAKE_LRCLIB_GET)
        return FakeResponse({}, status_code=404)
    if "/api/search" in url:
        return FakeResponse([], status_code=200)
    if streams_mod.CHARTS_API in url:
        return FakeResponse(FAKE_CHART)
    raise AssertionError(f"URL inattendue: {url}")


class TestPipelineEndToEnd(unittest.TestCase):
    def test_depuis_le_chart(self):
        """Top Spotify Charts -> dataset complet (paroles trouvées ou non)."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            out_csv = tmp / "out" / "dataset.csv"
            out_json = tmp / "out" / "dataset.json"

            with mock.patch.object(requests.Session, "get", fake_get):
                rc = run_pipeline.main(
                    [
                        "--chart", "global", "weekly", "regional", "10",
                        "--out", str(out_csv),
                        "--json",
                        "--delay", "0",
                        "--no-cache",
                    ]
                )
            self.assertEqual(rc, 0)

            # --- CSV ---
            with open(out_csv, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)

            row = next(r for r in rows if r["titre"] == "Titre Test")
            self.assertEqual(row["artiste"], "Artiste Test")
            self.assertEqual(row["streams"], "1234567")
            self.assertEqual(row["langue"], "fr")  # auto-détecté
            self.assertEqual(row["paroles_trouvees"], "True")
            self.assertEqual(row["paroles_synchonisees"], "True")
            counts = json.loads(row["syllabes_par_ligne"])
            self.assertEqual(len(counts), 2)
            self.assertEqual(int(row["nb_lignes"]), 2)
            self.assertEqual(int(row["total_syllabes"]), sum(counts))
            self.assertEqual(float(row["moy_syllabes_par_ligne"]), sum(counts) / 2)
            self.assertEqual(float(row["duree_secondes"]), 200.0)
            self.assertAlmostEqual(
                float(row["debit_syllabes_par_seconde"]), sum(counts) / 200.0, places=3
            )
            # ⚠️ Aucune parole dans le dataset (droit d'auteur)
            self.assertNotIn("danse", json.dumps(row, ensure_ascii=False))

            # Le titre sans paroles (404 LRCLIB) est quand même listé, avec
            # ses streams venus du chart ("987,654" -> 987654)
            row2 = next(r for r in rows if r["titre"] == "Autre Titre")
            self.assertEqual(row2["paroles_trouvees"], "False")
            self.assertEqual(row2["nb_lignes"], "0")
            self.assertEqual(row2["streams"], "987654")

            # --- JSON ---
            data = json.loads(out_json.read_text(encoding="utf-8"))
            row_json = next(r for r in data if r["titre"] == "Titre Test")
            self.assertEqual(row_json["syllabes_par_ligne"], counts)

    def test_depuis_csv_manuel(self):
        """Mode liste manuelle : --input + streams via --streams-csv."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            input_csv = tmp / "chansons.csv"
            input_csv.write_text(
                "artiste,titre,langue\nArtiste Test,Titre Test,fr\n",
                encoding="utf-8",
            )
            streams_csv = tmp / "streams.csv"
            streams_csv.write_text(
                "artiste,titre,streams\nArtiste Test,Titre Test,42000\n",
                encoding="utf-8",
            )
            out_csv = tmp / "dataset.csv"

            # Les lecteurs de CSV d'entrée
            songs = load_songs_csv(input_csv)
            self.assertEqual(
                songs,
                [{"artiste": "Artiste Test", "titre": "Titre Test", "langue": "fr"}],
            )
            idx = load_streams_csv(streams_csv)
            self.assertEqual(len(idx), 1)

            with mock.patch.object(requests.Session, "get", fake_get):
                rc = run_pipeline.main(
                    [
                        "--input", str(input_csv),
                        "--streams-csv", str(streams_csv),
                        "--lang", "fr",
                        "--out", str(out_csv),
                        "--delay", "0",
                        "--no-cache",
                    ]
                )
            self.assertEqual(rc, 0)
            with open(out_csv, newline="", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["streams"], "42000")
            self.assertEqual(rows[0]["langue"], "fr")
            self.assertEqual(rows[0]["paroles_trouvees"], "True")


if __name__ == "__main__":
    unittest.main()
