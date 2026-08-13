import { prisma } from "@/lib/prisma";
import SessionBoard from "@/components/SessionBoard";
import GeneratePanel from "@/components/GeneratePanel";
import type { ExerciseDto, PlanDto, SetDto, Split, ExoKind } from "@/lib/types";

export const dynamic = "force-dynamic";

export default async function Home() {
  const [rawExercises, sessions, rawPlans] = await Promise.all([
    prisma.exercise.findMany({
      orderBy: { order: "asc" },
      include: { sets: { include: { session: true } } },
    }),
    prisma.session.findMany({ orderBy: { date: "desc" } }),
    prisma.plan.findMany({ orderBy: { createdAt: "desc" }, take: 10 }),
  ]);

  // ---- Mapping vers DTO sérialisables pour les composants client ----
  const dtos: ExerciseDto[] = rawExercises.map((e) => {
    const bySession = new Map<string, { date: Date; sets: typeof e.sets }>();
    for (const s of e.sets) {
      const cur = bySession.get(s.sessionId);
      if (cur) cur.sets.push(s);
      else bySession.set(s.sessionId, { date: s.session.date, sets: [s] });
    }
    const sessionsDesc = [...bySession.values()].sort(
      (a, b) => b.date.getTime() - a.date.getTime()
    );

    const todayStart = new Date();
    todayStart.setHours(0, 0, 0, 0);

    const toDto = (s: (typeof e.sets)[number]): SetDto => ({
      id: s.id,
      setNumber: s.setNumber,
      weight: s.weight,
      reps: s.reps,
      note: s.note,
      date: s.doneAt.toISOString(),
    });

    const last = sessionsDesc[0];
    const lastSets = last
      ? [...last.sets].sort((a, b) => a.setNumber - b.setNumber).map(toDto)
      : [];
    const todaySets = last && last.date >= todayStart ? lastSets : [];

    const history = [...sessionsDesc].reverse().map((sess) => {
      const best = sess.sets.reduce((acc, s) =>
        s.weight > acc.weight || (s.weight === acc.weight && s.reps > acc.reps) ? s : acc
      );
      return { date: sess.date.toISOString(), weight: best.weight, reps: best.reps };
    });

    return {
      id: e.id,
      name: e.name,
      split: e.split as Split,
      kind: e.kind as ExoKind,
      lastSessionDate: last ? last.date.toISOString() : null,
      lastSets,
      todaySets,
      history,
    };
  });

  const upper = dtos.filter((e) => e.split === "UPPER");
  const lower = dtos.filter((e) => e.split === "LOWER");

  // ---- Stats header ----
  const lastSession = sessions[0];
  const daysSince = lastSession
    ? Math.max(0, Math.floor((Date.now() - lastSession.date.getTime()) / 86_400_000))
    : null;
  const cutoff = Date.now() - 14 * 86_400_000;
  const recentSessions = sessions.filter((s) => s.date.getTime() >= cutoff);
  let tonnage = 0;
  for (const e of rawExercises)
    for (const s of e.sets) if (s.doneAt.getTime() >= cutoff) tonnage += s.weight * s.reps;

  const plans: PlanDto[] = rawPlans.map((p) => ({
    id: p.id,
    createdAt: p.createdAt.toISOString(),
    split: p.split as Split,
    context: p.context,
    raw: p.raw,
  }));

  return (
    <main className="mx-auto max-w-7xl px-4 pb-44 sm:px-6">
      <header className="pb-8 pt-10">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-zinc-50">
              OVERLOAD<span className="text-lime-400">.</span>
            </h1>
            <p className="mt-1 text-sm text-zinc-500">
              Split Upper / Lower · Homme · 1m84 · 71kg · Objectif : prise de masse
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Stat
              label="Dernière séance"
              value={lastSession ? (lastSession.split === "UPPER" ? "Upper" : "Legs") : "—"}
              sub={daysSince === null ? "aucune" : daysSince === 0 ? "aujourd'hui" : `il y a ${daysSince} j`}
            />
            <Stat label="Séances · 14 j" value={String(recentSessions.length)} />
            <Stat
              label="Volume · 14 j"
              value={`${(tonnage / 1000).toLocaleString("fr-FR", { maximumFractionDigits: 1 })} t`}
            />
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <SessionBoard upper={upper} lower={lower} />
        </div>
        <div className="xl:sticky xl:top-6 xl:self-start">
          <GeneratePanel plans={plans} />
          <p className="mt-3 px-1 text-[11px] leading-relaxed text-zinc-600">
            💡 Avant de générer, précise ton contexte dans « Consignes » : reprise après 11 jours
            de pause, fatigue, douleur… L&apos;IA adaptera la surcharge en conséquence.
          </p>
        </div>
      </div>
    </main>
  );
}

function Stat({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="min-w-[130px] rounded-2xl border border-zinc-800 bg-zinc-900/60 px-4 py-3">
      <div className="text-[11px] uppercase tracking-wider text-zinc-500">{label}</div>
      <div className="mt-0.5 text-lg font-semibold text-zinc-100">{value}</div>
      {sub && <div className="text-[11px] text-zinc-500">{sub}</div>}
    </div>
  );
}
