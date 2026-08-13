# 🏋️ OVERLOAD — Workout Tracker + Coach IA (Gemini)

Suivi de musculation Upper/Lower avec graphiques de progression, chrono de repos automatique, saisie de perfs (poids/reps/notes) et génération de la prochaine séance par IA avec surcharge progressive.

## Stack
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS (UI dark)
- Prisma + SQLite (zéro config)
- Google Gemini SDK (gemini-1.5-flash par défaut)
- Recharts (courbes de progression)

## Installation (5 minutes)
1. npm install
2. cp .env.example .env  → colle ta clé GEMINI_API_KEY
   (gratuit sur https://aistudio.google.com/app/apikey)
3. npm run setup   → génère le client Prisma, crée la base SQLite, injecte les données de démo
4. npm run dev     → http://localhost:3000

## Commandes
- npm run dev        : serveur de dev
- npm run db:seed    : réinjecter les données de démo (modifie prisma/seed.ts pour TES exercices)
- npm run db:studio  : explorer la base (Prisma Studio)

## Comment marche le bouton "Générer la prochaine séance"
1. Le backend /api/generate lit tout l'historique (dernières perfs par exercice) dans SQLite.
2. Il formate l'historique + le nombre de jours depuis la dernière séance + TES consignes,
   et envoie le tout à Gemini avec le System Prompt "coach hypertrophie" (lib/prompt.ts).
3. Gemini répond en texte BRUT, format :  Exo : Poids x reps | Repos : temps
4. Le plan est sauvegardé (table Plan) et affiché tel quel, lisible à la salle.

## Préciser un contexte à l'IA (IMPORTANT)
Dans le champ "Consignes pour l'IA" (colonne de droite), écris par exemple :
- "ça fait 11 jours que je ne suis pas allé à la salle"
- "légère douleur à l'épaule droite, prudent sur le développé"
- "je suis très fatigué cette semaine, fais une séance light"
Ces consignes sont injectées comme PRIORITAIRES dans le prompt, et le délai depuis
ta dernière séance est de toute façon envoyé automatiquement à l'IA.

## Changer de modèle IA
Dans .env : GEMINI_MODEL=gemini-1.5-pro  (ou gemini-2.0-flash, etc.)
