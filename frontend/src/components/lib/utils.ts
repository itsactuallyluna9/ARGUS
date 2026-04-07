import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const clampScore = (score: number) => Math.max(0, Math.min(100, score));

export const getGoodnessScore = (score: number, higherIsBetter: boolean) => {
  const safeScore = clampScore(score);
  return higherIsBetter ? safeScore : 100 - safeScore;
};

export const getScoreDotColorClass = (
  score: number | null | undefined,
  higherIsBetter = true,
) => {
  if (score == null) return "bg-muted";

  const goodnessScore = getGoodnessScore(score, higherIsBetter);

  if (goodnessScore === 100) return "bg-indigo-500 dark:bg-indigo-400";
  if (goodnessScore >= 90) return "bg-emerald-500 dark:bg-emerald-400";
  if (goodnessScore >= 80) return "bg-green-500 dark:bg-green-400";
  if (goodnessScore >= 60) return "bg-lime-500 dark:bg-lime-400";
  if (goodnessScore >= 40) return "bg-amber-500 dark:bg-amber-400";
  if (goodnessScore >= 20) return "bg-orange-500 dark:bg-orange-400";
  if (goodnessScore >= 10) return "bg-rose-500 dark:bg-rose-400";
  return "bg-red-600 dark:bg-red-500";
};

export const getScoreBarColorClass = (score: number, higherIsBetter: boolean) => {
  const goodnessScore = getGoodnessScore(score, higherIsBetter);

  if (goodnessScore === 100) return "bg-indigo-500 dark:bg-indigo-400";
  if (goodnessScore >= 90) return "bg-emerald-500 dark:bg-emerald-400";

  if (goodnessScore >= 80) return "bg-green-500 dark:bg-green-400";
  if (goodnessScore >= 60) return "bg-lime-500 dark:bg-lime-400";
  if (goodnessScore >= 40) return "bg-amber-500 dark:bg-amber-400";

  if (goodnessScore >= 20) return "bg-orange-500 dark:bg-orange-400";
  if (goodnessScore >= 10) return "bg-rose-500 dark:bg-rose-400";
  return "bg-red-600 dark:bg-red-500";
};
