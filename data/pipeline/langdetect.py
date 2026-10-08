"""Détection simple français vs anglais (heuristique par mots-outils).

Suffisant pour choisir le dictionnaire pyphen. Pour un corpus hétérogène,
passe `--lang fr` ou `--lang en` explicitement au pipeline.
"""

from __future__ import annotations

import re
from collections import Counter

_STOPWORDS = {
    "fr": {
        "le", "la", "les", "un", "une", "des", "du", "de", "et", "est", "en",
        "que", "qui", "dans", "pour", "pas", "sur", "avec", "je", "tu", "il",
        "elle", "nous", "vous", "ils", "elles", "ce", "cette", "son", "sa", "ses",
        "mon", "ma", "mes", "ton", "ta", "tes", "au", "aux", "mais", "ou", "où",
        "ne", "se", "te", "si", "y", "à", "plus", "moins", "tout", "tous",
    },
    "en": {
        "the", "a", "an", "and", "is", "in", "that", "which", "for", "not",
        "with", "i", "you", "he", "she", "we", "they", "it", "this", "his",
        "her", "their", "my", "your", "at", "on", "but", "or", "if", "so",
        "be", "to", "of", "have", "has", "do", "does", "me", "him", "us",
        "them", "all", "no", "yes", "what", "when", "will", "would", "can",
    },
}

_WORD_RE = re.compile(r"[a-zàâäéèêëîïôöùûüç']+", re.IGNORECASE)


def detect_language(text: str, default: str = "fr") -> str:
    """Retourne 'fr' ou 'en' selon le score de mots-outils (match nul -> default)."""
    words = [w.lower() for w in _WORD_RE.findall(text)]
    if not words:
        return default
    scores = Counter()
    for w in words:
        for lang, stops in _STOPWORDS.items():
            if w in stops:
                scores[lang] += 1
    if not scores:
        return default
    best = scores.most_common(1)[0][0]
    return best
