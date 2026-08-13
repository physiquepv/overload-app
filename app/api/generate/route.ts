import { NextRequest, NextResponse } from "next/server";
import { GoogleGenerativeAI } from "@google/generative-ai";
import { prisma } from "@/lib/prisma";
import { SYSTEM_PROMPT } from "@/lib/prompt";

export const runtime = "nodejs";
export const maxDuration = 60;

// POST /api/generate  { split: "UPPER" | "LOWER", context?: string }
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const split = body.split === "LOWER" ? "LOWER" : "UPPER";
    const context = typeof body.context === "string" ? body.context.trim() : "";

    const key = process.env.GEMINI_API_KEY;
    if (!key) {
      return NextResponse.json(
        { ok: false, error: "GEMINI_API_KEY manquante. Ajoute-la dans le fichier .env." },
        { status: 500 }
      );
    }

    // ---- 1. Récupération de l'historique du split ----
    const exercises = await prisma.exercise.findMany({
      where: { split },
      orderBy: { order: "asc" },
      include: { sets: { include: { session: true } } },
    });

    // ---- 2. Formatage texte pour l'IA ----
    const blocks: string[] = [];
    let lastGlobal: Date | null = null;

    for (const e of exercises) {
      const bySession = new Map<string, { date: Date; sets: typeof e.sets }>();
      for (const s of e.sets) {
        const cur = bySession.get(s.sessionId);
        if (cur) cur.sets.push(s);
        else bySession.set(s.sessionId, { date: s.session.date, sets: [s] });
      }
      const sess = [...bySession.values()]
        .sort((a, b) => b.date.getTime() - a.date.getTime())
        .slice(0, 3); // 3 dernières séances max par exercice

      if (sess.length === 0) {
        blocks.push(`${e.name} : aucun historique`);
        continue;
      }
      if (!lastGlobal || sess[0].date > lastGlobal) lastGlobal = sess[0].date;

      const lines = sess.map((s) => {
        const sorted = [...s.sets].sort((a, b) => a.setNumber - b.setNumber);
        const repsStr = sorted.map((x) => x.reps).join(", ");
        const weights = [...new Set(sorted.map((x) => x.weight))];
        const weightStr = weights.length === 1 ? `${weights[0]}kg` : weights.map((w) => `${w}kg`).join("/");
        const notes = sorted.map((x) => x.note).filter(Boolean) as string[];
        const noteStr = notes.length ? ` | Notes : "${notes.join(" ; ")}"` : "";
        const dStr = s.date.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" });
        return `- ${dStr} → ${weightStr} : ${repsStr}${noteStr}`;
      });

      blocks.push(
        `${e.name} (${e.kind === "POLY" ? "polyarticulaire" : "isolation"}) :\n${lines.join("\n")}`
      );
    }

    const daysSince = lastGlobal
      ? Math.floor((Date.now() - lastGlobal.getTime()) / 86_400_000)
      : null;

    // ---- 3. Construction du prompt utilisateur ----
    const splitLabel = split === "UPPER" ? "UPPER (Haut du corps)" : "LOWER (Jambes)";
    let userPrompt = `PROFIL : Homme, 1m84, 71kg, objectif prise de masse. Programme split Upper / Lower.
SÉANCE À GÉNÉRER : ${splitLabel}
${
  daysSince !== null
    ? `Dernière séance enregistrée il y a ${daysSince} jour(s).`
    : "Aucune séance enregistrée pour le moment."
}

HISTORIQUE RÉCENT (par exercice, du plus récent au plus ancien) :
${blocks.join("\n\n")}
`;

    if (context) {
      userPrompt += `
CONSIGNES PARTICULIÈRES DE L'UTILISATEUR (PRIORITAIRES — adapte la séance en conséquence, tout en respectant strictement le format de sortie) :
"${context}"
`;
    }

    userPrompt += `
Génère maintenant la prochaine séance. Ta réponse doit contenir UNIQUEMENT le format de sortie défini, sans introduction ni conclusion.`;

    // ---- 4. Appel Gemini avec le System Prompt coach ----
    const genAI = new GoogleGenerativeAI(key);
    const model = genAI.getGenerativeModel({
      model: process.env.GEMINI_MODEL || "gemini-1.5-flash",
      systemInstruction: SYSTEM_PROMPT,
    });

    const out = await model.generateContent(userPrompt);
    const raw = out.response.text().trim();

    if (!raw) {
      return NextResponse.json(
        { ok: false, error: "Réponse vide de l'IA. Réessaie ou change de modèle." },
        { status: 502 }
      );
    }

    // ---- 5. Sauvegarde du plan + renvoi du texte brut ----
    const plan = await prisma.plan.create({
      data: { split, context: context || null, raw },
    });

    return NextResponse.json({
      ok: true,
      plan: {
        id: plan.id,
        raw: plan.raw,
        split: plan.split,
        context: plan.context,
        createdAt: plan.createdAt.toISOString(),
      },
    });
  } catch (e: any) {
    console.error("[generate]", e);
    return NextResponse.json(
      { ok: false, error: e?.message || "Erreur lors de l'appel à l'IA." },
      { status: 500 }
    );
  }
}
