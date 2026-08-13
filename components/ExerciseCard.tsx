"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import ProgressChart from "@/components/ProgressChart";
import type { ExerciseDto } from "@/lib/types";

const QUICK_NOTES = ["Échec", "Essoufflé", "Douleur", "Facile", "RAS"];

export default function ExerciseCard({
  exo,
  onLogged,
}: {
  exo: ExerciseDto;
  onLogged: (restSeconds: number) => void;
}) {
  const router = useRouter();
  const last = exo.lastSets[0];
  const [weight, setWeight] = useState(last ? String(last.weight) : "");
  const [reps, setReps] = useState(last ? String(last.reps) : "");
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const restSeconds = exo.kind === "POLY" ? 150 : 90; // 2:30 poly / 1:30 iso

  async function submit() {
    const w = parseFloat(weight.replace(",", "."));
    const r = parseInt(reps, 10);
    if (!Number.isFinite(w) || w <= 0 || !Number.isFinite(r) || r <= 0) {
      setError("Poids / reps invalides");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/log", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ exerciseId: exo.id, weight: w, reps: r, note: note.trim() || null }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Erreur");
      setNote("");
      router.refresh();
      onLogged(restSeconds); // lance le chrono de repos automatiquement
    } catch (e: any) {
      setError(e?.message || "Erreur lors de l'enregistrement");
    } finally {
      setBusy(false);
    }
  }

  const lastLabel = exo.lastSessionDate
    ? new Date(exo.lastSessionDate).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" })
    : null;
  const lastNotes = [...new Set(exo.lastSets.map((s) => s.note).filter(Boolean))] as string[];
  const todayCount = exo.todaySets.length;

  return (
    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-semibold text-zinc-100">{exo.name}</h3>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            <span
              className={`rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                exo.kind === "POLY"
                  ? "border-sky-400/30 bg-sky-400/10 text-sky-300"
                  : "border-violet-400/30 bg-violet-400/10 text-violet-300"
              }`}
            >
              {exo.kind === "POLY" ? "Poly · Repos 2:30" : "Iso · Repos 1:30"}
            </span>
            {lastLabel && exo.lastSets.length > 0 && (
              <span className="text-xs text-zinc-500">
                Dernière ({lastLabel}) :{" "}
                <span className="font-medium text-zinc-300">{exo.lastSets[0].weight}kg</span> ×{" "}
                {exo.lastSets.map((s) => s.reps).join(" · ")}
              </span>
            )}
          </div>
          {lastNotes.length > 0 && (
            <p className="mt-1 text-[11px] italic text-amber-400/80">📝 {lastNotes.join(" · ")}</p>
          )}
        </div>
        {todayCount > 0 && (
          <span className="shrink-0 rounded-full border border-lime-400/20 bg-lime-400/10 px-2.5 py-1 text-[11px] font-medium text-lime-300">
            {todayCount} série{todayCount > 1 ? "s" : ""} aujourd&apos;hui
          </span>
        )}
      </div>

      {exo.history.length > 1 && (
        <div className="mt-3">
          <ProgressChart data={exo.history} />
        </div>
      )}

      {todayCount > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {exo.todaySets.map((s) => (
            <span
              key={s.id}
              className="rounded-lg border border-zinc-700 bg-zinc-800/80 px-2.5 py-1 text-xs text-zinc-300"
            >
              #{s.setNumber} · {s.weight}kg × {s.reps}
              {s.note ? ` · ${s.note}` : ""}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex flex-col gap-2 sm:flex-row">
        <div className="flex gap-2">
          <div className="relative w-28">
            <input
              inputMode="decimal"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="20"
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 pr-10 text-sm focus:border-lime-400/60 focus:outline-none"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">kg</span>
          </div>
          <div className="relative w-24">
            <input
              inputMode="numeric"
              value={reps}
              onChange={(e) => setReps(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && submit()}
              placeholder="12"
              className="w-full rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 pr-11 text-sm focus:border-lime-400/60 focus:outline-none"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-zinc-500">reps</span>
          </div>
        </div>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Note (échec, essoufflé, douleur…)"
          className="flex-1 rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2 text-sm placeholder:text-zinc-600 focus:border-lime-400/60 focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={busy}
          className="rounded-xl bg-lime-400 px-4 py-2 text-sm font-bold text-zinc-950 transition hover:bg-lime-300 disabled:opacity-60"
        >
          {busy ? "…" : "+ Valider série"}
        </button>
      </div>

      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        {QUICK_NOTES.map((n) => (
          <button
            key={n}
            onClick={() => setNote((prev) => (prev === n ? "" : n))}
            className={`rounded-full border px-2.5 py-1 text-[11px] transition ${
              note === n
                ? "border-lime-400/60 bg-lime-400/10 text-lime-300"
                : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-600"
            }`}
          >
            {n}
          </button>
        ))}
        {error && <span className="ml-1 text-xs text-red-400">{error}</span>}
      </div>
    </div>
  );
}
