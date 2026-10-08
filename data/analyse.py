#!/usr/bin/env python3
"""Analyse exploratoire du dataset : y a-t-il un lien entre le succès (streams)
et la métrique de syllabes (débit, moyenne par ligne, total) ?

Stdlib uniquement. Exemple :

  python analyse.py output/dataset_syllabes.csv
  python analyse.py output/dataset_syllabes.csv --json output/rapport.json
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path

METRIQUES = {
    "debit_syllabes_par_seconde": "Débit (syll/s)",
    "moy_syllabes_par_ligne": "Moyenne syll/lignes",
    "total_syllabes": "Total syllabes",
    "nb_lignes": "Nb lignes",
}


def pearson(xs, ys) -> float | None:
    """Coefficient de corrélation de Pearson (None si variance nulle)."""
    n = len(xs)
    if n < 3:
        return None
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return None
    return cov / math.sqrt(vx * vy)


def load_rows(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Analyse streams vs syllabes.")
    p.add_argument("dataset", type=Path, help="CSV produit par run_pipeline.py")
    p.add_argument("--json", type=Path, default=None, help="Export du rapport en JSON.")
    args = p.parse_args(argv)

    rows = load_rows(args.dataset)
    completes = [
        r for r in rows
        if r.get("paroles_trouvees") == "True"
        and r.get("streams")
        and r["streams"].isdigit()
    ]
    print(f"{len(completes)}/{len(rows)} lignes exploitables "
          f"(paroles trouvées + streams connus)\n")
    if len(completes) < 3:
        print("Pas assez de données pour une corrélation (il en faut >= 3).")
        return 1

    streams = [int(r["streams"]) for r in completes]

    print("Corrélation de Pearson avec les streams (r entre -1 et +1) :")
    rapport = {"nb_lignes_exploitables": len(completes), "correlations": {}}
    for col, label in METRIQUES.items():
        paires = [(int(r["streams"]), float(r[col])) for r in completes if r.get(col)]
        if len(paires) < 3:
            continue
        xs = [s for s, _ in paires]
        ys = [v for _, v in paires]
        r = pearson(xs, ys)
        if r is None:
            continue
        rapport["correlations"][col] = round(r, 3)
        fleche = "↗" if r > 0.1 else ("↘" if r < -0.1 else "→")
        print(f"  {fleche} {label:24s} r = {r:+.3f}")

    print("\nTop 5 par métrique :")
    for col, label in METRIQUES.items():
        top = sorted(
            (r for r in completes if r.get(col)),
            key=lambda r: float(r[col]),
            reverse=True,
        )[:5]
        if not top:
            continue
        print(f"  {label} :")
        for r in top:
            print(f"    {float(r[col]):>10.2f}  {r['artiste']} — {r['titre']} "
                  f"({int(r['streams']):,} streams)".replace(",", " "))

    if args.json:
        args.json.write_text(
            json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\nRapport écrit : {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
