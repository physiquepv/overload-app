export type Split = "UPPER" | "LOWER";
export type ExoKind = "POLY" | "ISO";

export interface SetDto {
  id: string;
  setNumber: number;
  weight: number;
  reps: number;
  note?: string | null;
  date: string;
}

export interface ExerciseDto {
  id: string;
  name: string;
  split: Split;
  kind: ExoKind;
  lastSessionDate: string | null;
  lastSets: SetDto[];
  todaySets: SetDto[];
  history: { date: string; weight: number; reps: number }[];
}

export interface PlanDto {
  id: string;
  createdAt: string;
  split: Split;
  context: string | null;
  raw: string;
}
