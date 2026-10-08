"""Récupération des nombres de streams.

L'API officielle Spotify ne donne qu'un score de « popularity » (0-100), pas
les vrais chiffres. Deux sources sont utilisées ici :

1. Spotify Charts (charts.spotify.com) : top officiel avec streams exacts,
   interrogeable en JSON (endpoint /api/charts/...) ou téléchargeable en CSV.
2. Un CSV manuel (colonnes : artiste, titre, streams) pour compléter.

Les deux sources sont indexées par une clé normalisée « artiste | titre ».
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from pathlib import Path
from typing import Dict, Optional

import requests

CHARTS_API = "https://charts.spotify.com/api/charts"
HEADERS = {
    "User-Agent": "overload-syllabes-pipeline/1.0 (https://github.com/physiquepv/overload-app)"
}


def normalize_key(artist: str, title: str) -> str:
    """Clé normalisée pour faire correspondre artiste/titre entre les sources."""
    def clean(s: str) -> str:
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))  # accents -> lettres
        s = s.lower()
        s = re.sub(r"[^a-z0-9 ]", " ", s)  # ponctuation -> espaces
        return re.sub(r"\s+", " ", s).strip()

    return f"{clean(artist)} | {clean(title)}"


def parse_streams_value(value) -> Optional[int]:
    """Accepte 1234567, '1,234,567', '1 234 567', '1.234.567' -> int."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value)
    s = re.sub(r"[^\d]", "", str(value))
    return int(s) if s else None


def fetch_spotify_chart(
    session: requests.Session,
    region: str = "global",
    period: str = "weekly",
    chart_type: str = "regional",
    timeout: float = 20.0,
) -> Dict[str, dict]:
    """Retourne {clé normalisée: {'streams': int, 'rank': int, 'artist': str, 'title': str}}.

    region : 'global', 'fr', 'us', ... (code pays ISO ou 'global')
    period : 'daily' ou 'weekly'
    chart_type : 'regional' (top titres) ou 'viral' (titres montants)
    """
    url = f"{CHARTS_API}/{region}/{chart_type}/{period}/latest"
    r = session.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    payload = r.json()

    out: Dict[str, dict] = {}
    for entry in payload.get("entries", []):
        artist = entry.get("artist_name") or entry.get("artistName") or ""
        title = entry.get("track_name") or entry.get("trackName") or ""
        streams = parse_streams_value(entry.get("streams"))
        if not artist or not title:
            continue
        out[normalize_key(artist, title)] = {
            "streams": streams,
            "rank": entry.get("rank"),
            "artist": artist,
            "title": title,
        }
    return out


def load_streams_csv(path: Path) -> Dict[str, dict]:
    """Charge un CSV manuel avec colonnes : artiste, titre, streams."""
    out: Dict[str, dict] = {}
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            artist = (row.get("artiste") or row.get("artist") or "").strip()
            title = (row.get("titre") or row.get("titre") or row.get("title") or "").strip()
            if not artist or not title:
                continue
            out[normalize_key(artist, title)] = {
                "streams": parse_streams_value(row.get("streams")),
                "rank": None,
                "artist": artist,
                "title": title,
            }
    return out


def save_chart_cache(chart: Dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    serialisable = {k: v for k, v in chart.items()}
    path.write_text(json.dumps(serialisable, ensure_ascii=False, indent=2), encoding="utf-8")


def load_chart_cache(path: Path) -> Optional[Dict[str, dict]]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    return None
