"""Récupération des paroles via l'API ouverte LRCLIB (https://lrclib.net).

LRCLIB fournit souvent des paroles synchronisées (format LRC, ligne par ligne
avec minutage), ce qui permet de calculer un débit en syllabes/seconde.

⚠️ Les paroles sont protégées par le droit d'auteur : ce module les utilise
uniquement en mémoire pour calculer des nombres. Le dataset final ne contient
que les comptages de syllabes, jamais les textes.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Optional

import requests

LRCLIB_API = "https://lrclib.net/api"
# LRCLIB demande explicitement un User-Agent identifiable.
HEADERS = {
    "User-Agent": "overload-syllabes-pipeline/1.0 (https://github.com/physiquepv/overload-app)"
}


class LyricsResult(dict):
    """Dict avec accès par attributs : r.plain_lyrics, r.synced_lyrics, r.duration."""

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def _cache_path(cache_dir: Optional[Path], artist: str, track: str) -> Optional[Path]:
    if cache_dir is None:
        return None
    key = hashlib.sha1(f"{artist.lower()}|{track.lower()}".encode()).hexdigest()[:16]
    return cache_dir / f"lrclib_{key}.json"


def _from_cache(path: Optional[Path]) -> Optional[LyricsResult]:
    if path and path.exists():
        try:
            return LyricsResult(json.loads(path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, OSError):
            return None
    return None


def _to_cache(path: Optional[Path], data: LyricsResult) -> None:
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def fetch_lyrics(
    session: requests.Session,
    artist: str,
    track: str,
    cache_dir: Optional[Path] = None,
    delay: float = 1.1,
    timeout: float = 15.0,
) -> Optional[LyricsResult]:
    """Retourne les paroles d'un titre, ou None si LRCLIB ne les connaît pas.

    Essaie d'abord /api/get (correspondance exacte), puis /api/search (flou).
    Respecte la limite de débit de LRCLIB (~1 req/s) via `delay`.
    """
    cached = _from_cache(_cache_path(cache_dir, artist, track))
    if cached is not None:
        return cached

    session.headers.update(HEADERS)
    data: Optional[dict] = None

    r = session.get(
        f"{LRCLIB_API}/get",
        params={"artist_name": artist, "track_name": track},
        timeout=timeout,
    )
    if r.status_code == 200:
        data = r.json()
    elif r.status_code == 404:
        time.sleep(delay)  # rate-limit LRCLIB avant la requête suivante
        r = session.get(
            f"{LRCLIB_API}/search",
            params={"artist_name": artist, "track_name": track},
            timeout=timeout,
        )
        if r.status_code == 200 and r.json():
            # Prend le meilleur candidat : paroles non instrumentales, les plus longues.
            candidates = [c for c in r.json() if not c.get("instrumental") and c.get("plainLyrics")]
            if candidates:
                data = max(candidates, key=lambda c: len(c.get("plainLyrics") or ""))

    if not data or not data.get("plainLyrics"):
        return None

    result = LyricsResult(
        artist_name=data.get("artistName", artist),
        track_name=data.get("trackName", track),
        album_name=data.get("albumName", ""),
        duration=data.get("duration"),  # secondes (float) ou None
        plain_lyrics=data.get("plainLyrics", ""),
        synced_lyrics=data.get("syncedLyrics"),  # format LRC ou None
        instrumental=bool(data.get("instrumental", False)),
    )
    _to_cache(_cache_path(cache_dir, artist, track), result)
    time.sleep(delay)  # rate-limit LRCLIB
    return result
