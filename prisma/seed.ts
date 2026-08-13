import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

const daysAgo = (n: number) => {
  const d = new Date();
  d.setDate(d.getDate() - n);
  d.setHours(18, 30, 0, 0);
  return d;
};

type SetSeed = { reps: number; note?: string };
type RowSeed = { name: string; weight: number; sets: SetSeed[] };

// ---- Catalogue d'exercices (modifie selon TON programme) ----
const EXERCISES = [
  { name: "Développé incliné haltères", split: "UPPER", kind: "POLY", order: 1 },
  { name: "Tirage vertical", split: "UPPER", kind: "POLY", order: 2 },
  { name: "Chest press", split: "UPPER", kind: "POLY", order: 3 },
  { name: "Rowing haltère", split: "UPPER", kind: "POLY", order: 4 },
  { name: "Élévations latérales haltères", split: "UPPER", kind: "ISO", order: 5 },
  { name: "Curl barre EZ", split: "UPPER", kind: "ISO", order: 6 },
  { name: "Extension triceps poulie", split: "UPPER", kind: "ISO", order: 7 },
  { name: "Leg press", split: "LOWER", kind: "POLY", order: 1 },
  { name: "RDL", split: "LOWER", kind: "POLY", order: 2 },
  { name: "Squat haltère (Goblet)", split: "LOWER", kind: "POLY", order: 3 },
  { name: "Leg extension", split: "LOWER", kind: "ISO", order: 4 },
  { name: "Leg curl assis", split: "LOWER", kind: "ISO", order: 5 },
  { name: "Mollets à la presse", split: "LOWER", kind: "ISO", order: 6 },
];

async function createSession(split: string, date: Date, rows: RowSeed[]) {
  const session = await prisma.session.create({ data: { split, date } });
  for (const row of rows) {
    const exo = await prisma.exercise.findUnique({ where: { name: row.name } });
    if (!exo) throw new Error(`Exercice introuvable : ${row.name}`);
    let i = 1;
    for (const s of row.sets) {
      await prisma.set.create({
        data: {
          sessionId: session.id,
          exerciseId: exo.id,
          setNumber: i++,
          weight: row.weight,
          reps: s.reps,
          note: s.note ?? null,
        },
      });
    }
  }
  console.log(`✔ Séance ${split} du ${date.toLocaleDateString("fr-FR")} créée`);
}

async function main() {
  await prisma.set.deleteMany();
  await prisma.session.deleteMany();
  await prisma.plan.deleteMany();

  for (const e of EXERCISES) {
    await prisma.exercise.upsert({
      where: { name: e.name },
      update: { split: e.split, kind: e.kind, order: e.order },
      create: e,
    });
  }

  // ---- UPPER · il y a 13 jours ----
  await createSession("UPPER", daysAgo(13), [
    { name: "Développé incliné haltères", weight: 18, sets: [{ reps: 10 }, { reps: 10 }, { reps: 8 }] },
    { name: "Tirage vertical", weight: 45, sets: [{ reps: 12 }, { reps: 11 }, { reps: 10 }] },
    { name: "Chest press", weight: 20, sets: [{ reps: 11 }, { reps: 10 }, { reps: 9, note: "essoufflé" }] },
    { name: "Rowing haltère", weight: 24, sets: [{ reps: 10 }, { reps: 10 }, { reps: 9 }] },
    { name: "Élévations latérales haltères", weight: 8, sets: [{ reps: 12 }, { reps: 12 }, { reps: 10 }] },
    { name: "Curl barre EZ", weight: 20, sets: [{ reps: 10 }, { reps: 9 }, { reps: 8 }] },
    { name: "Extension triceps poulie", weight: 15, sets: [{ reps: 12 }, { reps: 11 }, { reps: 11 }] },
  ]);

  // ---- LOWER · il y a 11 jours ----
  await createSession("LOWER", daysAgo(11), [
    { name: "Leg press", weight: 120, sets: [{ reps: 10 }, { reps: 10 }, { reps: 10 }] },
    { name: "RDL", weight: 60, sets: [{ reps: 10 }, { reps: 9 }, { reps: 9, note: "bon étirement ischios" }] },
    { name: "Squat haltère (Goblet)", weight: 24, sets: [{ reps: 12 }, { reps: 11 }, { reps: 10, note: "très essoufflé" }] },
    { name: "Leg extension", weight: 40, sets: [{ reps: 12 }, { reps: 11 }, { reps: 10 }] },
    { name: "Leg curl assis", weight: 35, sets: [{ reps: 11 }, { reps: 10 }, { reps: 10 }] },
    { name: "Mollets à la presse", weight: 60, sets: [{ reps: 15 }, { reps: 14 }, { reps: 12 }] },
  ]);

  // ---- UPPER · il y a 7 jours ----
  await createSession("UPPER", daysAgo(7), [
    { name: "Développé incliné haltères", weight: 20, sets: [{ reps: 11 }, { reps: 10 }, { reps: 9 }] },
    { name: "Tirage vertical", weight: 50, sets: [{ reps: 12 }, { reps: 12 }, { reps: 11 }] },
    { name: "Chest press", weight: 22.5, sets: [{ reps: 12 }, { reps: 11 }, { reps: 10 }] },
    { name: "Rowing haltère", weight: 26, sets: [{ reps: 11 }, { reps: 10 }, { reps: 10 }] },
    { name: "Élévations latérales haltères", weight: 10, sets: [{ reps: 12 }, { reps: 12 }, { reps: 12, note: "propre, aucun élan" }] },
    { name: "Curl barre EZ", weight: 20, sets: [{ reps: 11 }, { reps: 10 }, { reps: 9 }] },
    { name: "Extension triceps poulie", weight: 17.5, sets: [{ reps: 12 }, { reps: 12 }, { reps: 11 }] },
  ]);

  // ---- LOWER · il y a 5 jours ----
  await createSession("LOWER", daysAgo(5), [
    { name: "Leg press", weight: 130, sets: [{ reps: 11 }, { reps: 10 }, { reps: 10, note: "lourd mais propre" }] },
    { name: "RDL", weight: 65, sets: [{ reps: 10 }, { reps: 10 }, { reps: 9 }] },
    { name: "Squat haltère (Goblet)", weight: 26, sets: [{ reps: 12 }, { reps: 12 }, { reps: 11, note: "essoufflé dernière série" }] },
    { name: "Leg extension", weight: 45, sets: [{ reps: 12 }, { reps: 12 }, { reps: 11 }] },
    { name: "Leg curl assis", weight: 40, sets: [{ reps: 12 }, { reps: 11 }, { reps: 10 }] },
    { name: "Mollets à la presse", weight: 65, sets: [{ reps: 15 }, { reps: 15 }, { reps: 13 }] },
  ]);

  console.log("🌱 Seed terminé.");
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
