import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OVERLOAD — Workout Tracker",
  description: "Suivi musculation Upper/Lower + coach IA (surcharge progressive)",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased">{children}</body>
    </html>
  );
}
