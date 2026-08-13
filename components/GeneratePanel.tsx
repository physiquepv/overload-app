"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import type { PlanDto, Split } from "@/lib/types";

export default function GeneratePanel({ plans }: { plans: PlanDto[] }) {
  const router = useRouter();
  const [split, setSplit] = useState<Split>("UPPER");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(plans[0]?.raw ?? null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  async function generate() {
    setLoading(true);
    setError(null);
    setCopied(false);
    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ split, context: context.trim() }),
      });
      const data = await res.json();
      if (!data.ok) throw new Error(data.error || "Erreur IA");
      setResult(data.plan.raw);
      router.refresh();
    } catch (e: any) {
      setError(e?.message || "Erreur lors de la génération");
    } finally {
      setLoading(false);
    }
  }

  async function copy() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard indisponible */
    }
  }

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/50 p-5">
      <h2 className="font-semibold text-zinc-100">
        🤖 Prochaine séance <span className="font-normal text-zinc-500">(Coach IA)</span>
      </h2>

      <div className="mt-4 grid grid-cols-2 gap-2">
        {(["UPPER", "LOWER"] as Split[]).map((s) => (
          <button
            key={s}
            onClick={() => setSplit(s)}
            className={`rounded-xl border px-3 py-2 text-sm font-medium transition ${
              split === s
                ? "border-lime-400/50 bg-lime-400/10 text-lime-300"
                : "border-zinc-800 bg-zinc-900 text-zinc-400 hover:border-zinc-700"
            }`}
          >
            {s === "UPPER" ? "Haut du corps" : "Jambes"}
          </button>
        ))}
      </div>

      <label className="mb-1.5 mt-4 block text-xs text-zinc-500">
        Consignes pour l&apos;IA (optionnel)
      </label>
      <textarea
        value={context}
        onChange={(e) => setContext(e.target.value)}
        rows={3}
        placeholder={
          "Ex : ça fait 11 jours que je ne suis pas allé à la salle.\nEx : légère douleur à l'épaule droite, prudent sur le développé.\nEx : je suis très fatigué cette semaine."
        }
        className="w-full resize-none rounded-xl border border-zinc-800 bg-zinc-900 px-3 py-2.5 text-sm placeholder:text-zinc-600 focus:border-lime-400/60 focus:outline-none"
      />

      <button
        onClick={generate}
        disabled={loading}
        className="mt-3 w-full rounded-xl bg-lime-400 py-3 text-sm font-bold text-zinc-950 transition hover:bg-lime-300 disabled:opacity-60"
      >
        {loading ? "⏳ Analyse de l'historique…" : "⚡ Générer la prochaine séance"}
      </button>

      {error && (
        <div className="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      {result && (
        <div className="mt-5">
          <div className="mb-2 flex items-center justify-between">
            <span className="text-xs uppercase tracking-wider text-zinc-500">
              Programme généré
            </span>
            <button
              onClick={copy}
              className="rounded-lg border border-zinc-800 px-2 py-1 text-xs text-zinc-400 transition hover:text-zinc-200"
            >
              {copied ? "✓ Copié" : "Copier"}
            </button>
          </div>
          <pre className="whitespace-pre-wrap rounded-xl border border-lime-400/20 bg-zinc-950 p-4 font-mono text-[13px] leading-relaxed text-zinc-100">
            {result}
          </pre>
        </div>
      )}

      {plans.length > 0 && (
        <div className="mt-4">
          <button
            onClick={() => setShowHistory((v) => !v)}
            className="text-xs text-zinc-500 transition hover:text-zinc-300"
          >
            {showHistory ? "▾ Masquer" : "▸ Voir"} l&apos;historique ({plans.length})
          </button>
          {showHistory && (
            <div className="mt-2 max-h-80 space-y-3 overflow-y-auto pr-1">
              {plans.map((p) => (
                <div key={p.id} className="rounded-xl border border-zinc-800 bg-zinc-950 p-3">
                  <div className="mb-1.5 text-[11px] text-zinc-500">
                    {p.split} ·{" "}
                    {new Date(p.createdAt).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "2-digit",
                    })}
                    {p.context ? ` · « ${p.context} »` : ""}
                  </div>
                  <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-zinc-400">
                    {p.raw}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </section>
  );
}
