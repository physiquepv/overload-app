#!/usr/bin/env python3
"""Point d'entrée CLI du pipeline « syllabes vs streams ».

Exemples :

  # À partir d'une liste de chansons
  python run_pipeline.py --input chansons.csv --out output/dataset_syllabes.csv

  # À partir du top Spotify Charts (50 premiers du global hebdo)
  python run_pipeline.py --chart global weekly regional 50 --out output/dataset_syllabes.csv

  # En forçant la langue et en exportant aussi du JSON
  python run_pipeline.py --input chansons.csv --lang fr --json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import requests

from pipeline.pipeline import (
    load_songs_csv,
    process_song,
    songs_from_chart,
    write_dataset,
)
from pipeline.streams import (
    fetch_spotify_chart,
    load_chart_cache,
    load_streams_csv,
    save_chart_cache,
)

DATA_DIR = Path(__file__).resolve().parent


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Dataset syllabes/ligne + streams Spotify.")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--input", type=Path, default=DATA_DIR / "chansons.csv",
                   help="CSV d'entrée (colonnes: artiste, titre, langue optionnelle).")
    src.add_argument("--chart", nargs=4, metavar=("REGION", "PERIOD", "TYPE", "LIMIT"),
                   help="Utilise le top Spotify Charts. Ex: --chart global weekly regional 50")
    p.add_argument("--streams-csv", type=Path, default=None,
                   help="CSV manuel de streams (artiste, titre, streams) en complément du chart.")
    p.add_argument("--lang", choices=["auto", "fr", "en"], default="auto",
                   help="Langue pour le comptage de syllabes (défaut: auto-détection).")
    p.add_argument("--out", type=Path, default=DATA_DIR / "output" / "dataset_syllabes.csv",
                   help="Chemin du CSV de sortie.")
    p.add_argument("--json", action="store_true", help="Exporte aussi un .json à côté du CSV.")
    p.add_argument("--delay", type=float, default=1.1,
                   help="Délai entre requêtes LRCLIB en secondes (rate-limit ~1 req/s).")
    p.add_argument("--no-cache", action="store_true", help="Désactive le cache local des paroles.")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    cache_dir = None if args.no_cache else DATA_DIR / ".cache"
    session = requests.Session()

    # --- Liste de chansons ---
    if args.chart:
        region, period, chart_type, limit = args.chart
        limit = int(limit)
        chart_cache = DATA_DIR / ".cache" / f"chart_{region}_{chart_type}_{period}.json"
        chart = None if args.no_cache else load_chart_cache(chart_cache)
        if chart is None:
            print(f"Téléchargement du chart Spotify : {region} / {chart_type} / {period} ...")
            chart = fetch_spotify_chart(session, region=region, period=period, chart_type=chart_type)
            if cache_dir is not None:
                save_chart_cache(chart, chart_cache)
        print(f"  -> {len(chart)} titres dans le chart")
        songs = songs_from_chart(chart, limit=limit)
    else:
        songs = load_songs_csv(args.input)
        print(f"{len(songs)} chansons dans {args.input}")
        chart = {}

    # --- Index des streams ---
    streams_index = dict(chart)
    if args.streams_csv:
        extra = load_streams_csv(args.streams_csv)
        print(f"{len(extra)} streams chargés depuis {args.streams_csv}")
        streams_index.update(extra)  # le CSV manuel a la priorité

    # --- Traitement ---
    rows = []
    for i, song in enumerate(songs, 1):
        print(f"[{i}/{len(songs)}] {song['artiste']} — {song['titre']} ...", flush=True)
        try:
            row = process_song(session, song, args.lang, streams_index,
                               cache_dir=cache_dir, delay=args.delay)
        except requests.RequestException as exc:
            print(f"    ! erreur réseau ({exc}) — titre ignoré")
            continue
        rows.append(row)
        if row["paroles_trouvees"]:
            print(f"    OK  {row['langue']}  {row['total_syllabes']} syllabes / "
                  f"{row['nb_lignes']} lignes  streams={row['streams']}")
        else:
            print(f"    --  pas de paroles trouvées  streams={row['streams']}")

    # --- Export ---
    out_json = args.out.with_suffix(".json") if args.json else None
    write_dataset(rows, args.out, out_json)
    trouves = sum(1 for r in rows if r["paroles_trouvees"])
    print(f"\nDataset écrit : {args.out} ({len(rows)} lignes, {trouves} avec paroles)")
    if out_json:
        print(f"Export JSON  : {out_json}")
    print("⚠️  Rappel : ce fichier ne contient que des NOMBRES de syllabes, pas les paroles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
