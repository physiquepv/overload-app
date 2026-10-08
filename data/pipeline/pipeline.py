"""Orchestration : liste de chansons -> dataset (titre, artiste, streams, langue,
syllabes_par_ligne + statistiques).

⚠️ Droit d'auteur : les paroles ne servent qu'à calculer des nombres en mémoire.
Le dataset exporté ne contient AUCUN texte de paroles, seulement les comptages.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

import requests

from . import lyrics as lyrics_mod
from . import streams as streams_mod
from .syllables import speech_rate, stats, syllables_per_line
from .langdetect import detect_language

DATASET_COLUMNS = [
    "titre",
    "artiste",
    "streams",
    "langue",
    "syllabes_par_ligne",
    "nb_lignes",
    "total_syllabes",
    "moy_syllabes_par_ligne",
    "ecart_type_syllabes",
    "duree_secondes",
    "debit_syllabes_par_seconde",
    "paroles_trouvees",
    "paroles_synchonisees",
]


# ---------------------------------------------------------------------------
# Entrées
# ---------------------------------------------------------------------------

def load_songs_csv(path: Path) -> List[dict]:
    """CSV d'entrée : colonnes 'artiste', 'titre' (+ 'langue' optionnelle)."""
    songs = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            artist = (row.get("artiste") or row.get("artist") or "").strip()
            title = (row.get("titre") or row.get("title") or "").strip()
            if not artist or not title:
                continue
            songs.append(
                {
                    "artiste": artist,
                    "titre": title,
                    "langue": (row.get("langue") or row.get("lang") or "").strip().lower() or None,
                }
            )
    return songs


def songs_from_chart(chart: Dict[str, dict], limit: Optional[int] = None) -> List[dict]:
    """Convertit un index de chart Spotify en liste de chansons (trié par rank)."""
    entries = sorted(
        chart.values(), key=lambda e: (e.get("rank") is None, e.get("rank") or 0)
    )
    if limit:
        entries = entries[:limit]
    return [{"artiste": e["artist"], "titre": e["title"], "langue": None} for e in entries]


# ---------------------------------------------------------------------------
# Traitement d'un titre
# ---------------------------------------------------------------------------

def row_from_lyrics(
    song: dict,
    lyrics: Optional[lyrics_mod.LyricsResult],
    lang_mode: str,
    streams_index: Dict[str, dict],
) -> dict:
    """Construit une ligne du dataset à partir du résultat LRCLIB (fonction pure,
    testable sans réseau)."""
    key = streams_mod.normalize_key(song["artiste"], song["titre"])
    stream_entry = streams_index.get(key)
    streams = stream_entry["streams"] if stream_entry else None

    if lyrics is None or lyrics.get("instrumental"):
        return {
            "titre": song["titre"],
            "artiste": song["artiste"],
            "streams": streams,
            "langue": None,
            "syllabes_par_ligne": None,
            "nb_lignes": 0,
            "total_syllabes": 0,
            "moy_syllabes_par_ligne": None,
            "ecart_type_syllabes": None,
            "duree_secondes": None,
            "debit_syllabes_par_seconde": None,
            "paroles_trouvees": False,
            "paroles_synchonisees": False,
        }

    lang = (song.get("langue") or lang_mode if lang_mode != "auto" else None) or detect_language(
        lyrics["plain_lyrics"]
    )
    counts = syllables_per_line(lyrics["plain_lyrics"], lang)
    s = stats(counts)
    synced = bool(lyrics.get("synced_lyrics"))

    return {
        "titre": lyrics.get("track_name") or song["titre"],
        "artiste": lyrics.get("artist_name") or song["artiste"],
        "streams": streams,
        "langue": lang,
        "syllabes_par_ligne": json.dumps(counts, ensure_ascii=False),
        **s,
        "duree_secondes": lyrics.get("duration"),
        "debit_syllabes_par_seconde": speech_rate(
            counts, lyrics.get("synced_lyrics"), lyrics.get("duration")
        ),
        "paroles_trouvees": True,
        "paroles_synchonisees": synced,
    }


def process_song(
    session: requests.Session,
    song: dict,
    lang_mode: str,
    streams_index: Dict[str, dict],
    cache_dir: Optional[Path] = None,
    delay: float = 1.1,
) -> dict:
    """Récupère les paroles (avec cache) puis construit la ligne du dataset."""
    found = lyrics_mod.fetch_lyrics(
        session, song["artiste"], song["titre"], cache_dir=cache_dir, delay=delay
    )
    return row_from_lyrics(song, found, lang_mode, streams_index)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def write_dataset(rows: List[dict], out_csv: Path, out_json: Optional[Path] = None) -> None:
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DATASET_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    if out_json is not None:
        out_json.parent.mkdir(parents=True, exist_ok=True)
        serialisable = []
        for row in rows:
            row = dict(row)
            if row.get("syllabes_par_ligne"):
                row["syllabes_par_ligne"] = json.loads(row["syllabes_par_ligne"])
            serialisable.append(row)
        out_json.write_text(
            json.dumps(serialisable, ensure_ascii=False, indent=2), encoding="utf-8"
        )
