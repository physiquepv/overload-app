"use client";

import { useState } from "react";
import ExerciseCard from "@/components/ExerciseCard";
import RestTimer from "@/components/RestTimer";
import type { ExerciseDto, Split } from "@/lib/types";

function fmt(sec: number) {
  return `${Math.floor(sec / 60)}:${String(sec % 60).padStart(2, "0")}`;
}

export default function SessionBoard({
  upper,
  lower,
}: {
  upper: ExerciseDto[];
  lower: ExerciseDto[];
}) {
  const [tab, setTab] = useState<Split>("UPPER");
  const [timerReq, setTimerReq] = useState<{ seconds: number; nonce: number } | null>(null);

  const startTimer = (seconds: number) =>
    setTimerReq((prev) => ({ seconds, nonce: (prev?.nonce ?? 0) + 1 }));

  const list = tab === "UPPER" ? upper : lower;

  return (
    <div>
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-xl border border-zinc-800 bg-zinc-900/60 p-1">
          {(["UPPER", "LOWER"] as Split[]).map((s) => (
            <button
              key={s}
              onClick={() => setTab(s)}
              className={`rounded-lg px-4 py-2 text-sm font-semibold transition ${
                tab === s ? "bg-lime-400 text-zinc-950" : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {s === "UPPER" ? "Haut du corps" : "Jambes"}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-1.5 text-xs text-zinc-500">
          ⏱ Chrono :
          {[90, 150, 180].map((s) => (
            <button
              key={s}
              onClick={() => startTimer(s)}
              className="rounded-lg border border-zinc-800 bg-zinc-900 px-2.5 py-1 font-medium text-zinc-300 transition hover:border-lime-400/50 hover:text-lime-300"
            >
              {fmt(s)}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        {list.map((e) => (
          <ExerciseCard key={e.id} exo={e} onLogged={startTimer} />
        ))}
      </div>

      <RestTimer request={timerReq} />
    </div>
  );
}
