# 📊 Pipeline « Syllabes vs Streams »

Récupère les **paroles** (LRCLIB) et les **streams** (Spotify Charts) de chansons,
compte les **syllabes par ligne** (français et anglais) et produit un dataset
prêt à être analysé.

> ⚠️ **Droit d'auteur** : les paroles sont protégées. Elles ne servent ici qu'à
> calculer des **nombres** en mémoire (et sont mises en cache localement le temps
> du run). **Le dataset exporté ne contient jamais les textes**, seulement les
> comptages de syllabes. Ne redistribue pas les paroles elles-mêmes.

## Installation

```bash
cd data
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Utilisation

### 1. Produire le dataset

```bash
# À partir d'une liste de chansons (édite data/chansons.csv)
.venv/bin/python run_pipeline.py --input chansons.csv --out output/dataset_syllabes.csv

# À partir du top Spotify Charts (ex: 50 premiers du global hebdo)
.venv/bin/python run_pipeline.py --chart global weekly regional 50 --out output/dataset_syllabes.csv

# Options utiles
#   --lang fr|en|auto   langue du comptage (défaut: auto-détection)
#   --json              exporte aussi un .json
#   --streams-csv FICHIER  complète les streams avec un CSV manuel (artiste,titre,streams)
#   --delay 1.1         délai entre requêtes LRCLIB (rate-limit ~1 req/s)
```

### 2. Analyser le dataset

```bash
.venv/bin/python analyse.py output/dataset_syllabes.csv
```

Corrélation de Pearson entre les streams et le débit (syll/s), la moyenne de
syllabes par ligne, etc. — pour voir s'il y a un lien entre la densité de
syllabes et le succès.

### 3. Tests (hors-ligne, aucun appel réseau)

```bash
.venv/bin/python -m unittest discover -s tests -v
```

## Structure du dataset

| colonne | description |
|---|---|
| `titre`, `artiste` | morceau (normalisé côté matching) |
| `streams` | nombre exact de streams (Spotify Charts ou CSV manuel) |
| `langue` | `fr` ou `en` (auto-détecté ou forcé) |
| `syllabes_par_ligne` | liste JSON, ex: `[5, 6, 4, 7]` |
| `nb_lignes`, `total_syllabes` | agrégats |
| `moy_syllabes_par_ligne`, `ecart_type_syllabes` | stats de distribution |
| `duree_secondes` | durée du morceau (LRCLIB) |
| `debit_syllabes_par_seconde` | total_syllabes / durée (grâce aux paroles synchronisées LRC) |
| `paroles_trouvees`, `paroles_synchonisees` | flags de qualité |

## Sources de données

| Donnée | Source | Pourquoi |
|---|---|---|
| Paroles (+ minutage) | **LRCLIB** (lrclib.net) | API gratuite et ouverte, paroles souvent synchronisées (LRC) |
| Streams exacts | **Spotify Charts** (charts.spotify.com) | l'API Spotify officielle ne donne qu'un score 0-100 |
| Streams (alternatif) | CSV manuel (`--streams-csv`) ou Kworb.net / datasets Kaggle | compléter quand le titre n'est pas dans le chart |

## Comptage des syllabes

- **Français** : hybride `pyphen` (fr_FR) + comptage des noyaux vocaliques avec
  gestion du « e » muet, des élisions et des nasales. Pyphen seul sous-compte
  les petits mots (« alors » → 1 au lieu de 2).
- **Anglais** : dictionnaire **CMU** via `pronouncing` (précis), fallback
  `pyphen` (en_US) si le mot est inconnu.
- **Plus précis (optionnel)** : pour du français phonétique exact, remplacer le
  compteur par `phonemizer` + espeak-ng (`pip install phonemizer`, paquet ES
  `espeak-ng`), compter les voyelles des phonèmes IPA. C'est plus lourd et moins
  utile pour des paroles chantées.

## Arborescence

```
data/
  run_pipeline.py     CLI principal (produit le dataset)
  analyse.py          analyse exploratoire (corrélation streams ↔ syllabes)
  chansons.csv        liste d'exemple (artiste, titre, langue)
  requirements.txt    dépendances Python
  pipeline/           code (lyrics, streams, syllables, langdetect, pipeline)
  tests/              tests unitaires + intégration (mock HTTP, hors-ligne)
  .cache/             cache local des appels API (gitignored)
  output/             datasets produits (gitignored)
```
