import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

// POST /api/log → enregistre une série (rattachée à la séance du jour du même split)
export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const exerciseId = String(body.exerciseId ?? "");
    const weight = Number(body.weight);
    const reps = Number(body.reps);
    const note =
      typeof body.note === "string" && body.note.trim() ? body.note.trim().slice(0, 300) : null;

    if (
      !exerciseId ||
      !Number.isFinite(weight) ||
      weight <= 0 ||
      !Number.isInteger(reps) ||
      reps <= 0
    ) {
      return NextResponse.json({ ok: false, error: "Données invalides" }, { status: 400 });
    }

    const exercise = await prisma.exercise.findUnique({ where: { id: exerciseId } });
    if (!exercise) {
      return NextResponse.json({ ok: false, error: "Exercice introuvable" }, { status: 404 });
    }

    const startOfDay = new Date();
    startOfDay.setHours(0, 0, 0, 0);
    const endOfDay = new Date(startOfDay);
    endOfDay.setDate(endOfDay.getDate() + 1);

    let session = await prisma.session.findFirst({
      where: { split: exercise.split, date: { gte: startOfDay, lt: endOfDay } },
      orderBy: { date: "desc" },
    });
    if (!session) {
      session = await prisma.session.create({ data: { split: exercise.split, date: new Date() } });
    }

    const setNumber =
      (await prisma.set.count({ where: { sessionId: session.id, exerciseId } })) + 1;

    const set = await prisma.set.create({
      data: { sessionId: session.id, exerciseId, setNumber, weight, reps, note },
    });

    return NextResponse.json({ ok: true, set: { id: set.id, setNumber: set.setNumber } });
  } catch {
    return NextResponse.json({ ok: false, error: "Erreur serveur" }, { status: 500 });
  }
}
