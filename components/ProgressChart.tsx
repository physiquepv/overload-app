"use client";

import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip } from "recharts";

export default function ProgressChart({
  data,
}: {
  data: { date: string; weight: number; reps: number }[];
}) {
  const points = data.map((p) => ({
    label: new Date(p.date).toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit" }),
    poids: p.weight,
    reps: p.reps,
  }));

  if (points.length < 2) return null;

  return (
    <div className="h-24 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 6, right: 6, bottom: 0, left: 0 }}>
          <XAxis
            dataKey="label"
            tick={{ fill: "#71717a", fontSize: 10 }}
            axisLine={{ stroke: "#27272a" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#71717a", fontSize: 10 }}
            axisLine={false}
            tickLine={false}
            width={40}
            domain={["dataMin - 2.5", "dataMax + 2.5"]}
          />
          <Tooltip
            contentStyle={{
              background: "#18181b",
              border: "1px solid #3f3f46",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelStyle={{ color: "#a1a1aa" }}
            formatter={(value: any, name: any, item: any) => [
              `${value} kg (${item?.payload?.reps} reps)`,
              "Meilleure série",
            ]}
          />
          <Line
            type="monotone"
            dataKey="poids"
            stroke="#a3e635"
            strokeWidth={2}
            dot={{ r: 2.5, fill: "#a3e635", strokeWidth: 0 }}
            activeDot={{ r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
