"use client";

import { useEffect, useRef, useState } from "react";

export type TimerRequest = { seconds: number; nonce: number } | null;

function beep(times = 3) {
  try {
    const Ctx = window.AudioContext || (window as any).webkitAudioContext;
    const ctx = new Ctx();
    for (let i = 0; i < times; i++) {
      const o = ctx.createOscillator();
      const g = ctx.createGain();
      o.connect(g);
      g.connect(ctx.destination);
      o.frequency.value = 880;
      const t = ctx.currentTime + i * 0.35;
      g.gain.setValueAtTime(0.0001, t);
      g.gain.exponentialRampToValueAtTime(0.4, t + 0.02);
      g.gain.exponentialRampToValueAtTime(0.0001, t + 0.3);
      o.start(t);
      o.stop(t + 0.32);
    }
  } catch {
    /* silencieux si audio bloqué */
  }
}

export default function RestTimer({ request }: { request: TimerRequest }) {
  const [total, setTotal] = useState(0);
  const [remaining, setRemaining] = useState(0);
  const [running, setRunning] = useState(false);
  const [done, setDone] = useState(false);
  const endRef = useRef<number>(0);

  // Démarrage / redémarrage à chaque demande (nonce)
  useEffect(() => {
    if (!request) return;
    endRef.current = Date.now() + request.seconds * 1000;
    setTotal(request.seconds);
    setRemaining(request.seconds);
    setRunning(true);
    setDone(false);
  }, [request]);

  // Tick
  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => {
      const r = Math.max(0, Math.round((endRef.current - Date.now()) / 1000));
      setRemaining(r);
      if (r <= 0) {
        setRunning(false);
        setDone(true);
        beep();
        if ("vibrate" in navigator) navigator.vibrate([200, 100, 200, 100, 400]);
      }
    }, 200);
    return () => clearInterval(id);
  }, [running]);

  function add(sec: number) {
    if (total <= 0) return;
    endRef.current += sec * 1000;
    setTotal((t) => Math.max(15, t + sec));
    const r = Math.max(0, Math.round((endRef.current - Date.now()) / 1000));
    setRemaining(r);
    if (r > 0) {
      setDone(false);
      setRunning(true);
    }
  }

  function stop() {
    setRunning(false);
    setDone(false);
    setTotal(0);
    setRemaining(0);
  }

  if (total <= 0) return null;

  const R = 54;
  const C = 2 * Math.PI * R;
  const progress = remaining / total;
  const mm = Math.floor(remaining / 60);
  const ss = String(remaining % 60).padStart(2, "0");

  return (
    <div className="pointer-events-none fixed inset-x-0 bottom-5 z-50 flex justify-center px-4">
      <div
        className={`pointer-events-auto flex items-center gap-4 rounded-2xl border px-5 py-4 shadow-2xl backdrop-blur-xl ${
          done ? "border-lime-400/60 bg-lime-950/70" : "border-zinc-700 bg-zinc-900/90"
        }`}
      >
        <div className="relative h-[120px] w-[120px]">
          <svg width="120" height="120" viewBox="0 0 120 120">
            <circle cx="60" cy="60" r={R} fill="none" stroke="#27272a" strokeWidth="8" />
            <circle
              cx="60"
              cy="60"
              r={R}
              fill="none"
              stroke={remaining <= 5 && !done ? "#fb7185" : "#a3e635"}
              strokeWidth="8"
              strokeLinecap="round"
              strokeDasharray={C}
              strokeDashoffset={C * (1 - progress)}
              transform="rotate(-90 60 60)"
              style={{ transition: "stroke-dashoffset 0.2s linear" }}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-3xl font-bold tabular-nums">
              {done ? "GO" : `${mm}:${ss}`}
            </span>
            <span className="text-[10px] uppercase tracking-widest text-zinc-500">
              {done ? "Reprends 💪" : "Repos"}
            </span>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex gap-2">
            <button
              onClick={() => add(-15)}
              className="rounded-xl border border-zinc-700 px-3 py-2 text-sm text-zinc-300 transition hover:bg-zinc-800"
            >
              −15s
            </button>
            <button
              onClick={() => add(15)}
              className="rounded-xl border border-zinc-700 px-3 py-2 text-sm text-zinc-300 transition hover:bg-zinc-800"
            >
              +15s
            </button>
          </div>
          {done ? (
            <button
              onClick={stop}
              className="animate-pulse rounded-xl bg-lime-400 px-4 py-2 text-sm font-bold text-zinc-950"
            >
              C&apos;est parti 🔥
            </button>
          ) : (
            <button
              onClick={stop}
              className="rounded-xl border border-zinc-700 px-4 py-2 text-sm text-zinc-300 transition hover:bg-zinc-800"
            >
              Arrêter
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
