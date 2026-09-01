import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: value < 1 ? 4 : 2,
    maximumFractionDigits: value < 1 ? 6 : 2,
    ...options,
  }).format(value);
}

export function formatCompactNumber(value: number): string {
  return new Intl.NumberFormat("en-US", {
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number, withSign = true): string {
  const sign = withSign && value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatUtcClock(date: Date): string {
  return date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    timeZone: "UTC",
    hour12: false,
  });
}

const TIME_AGO_UNITS = {
  en: { justNow: "just now", minute: "m ago", hour: "h ago", day: "d ago" },
  // Abbreviated units ("мин.", "ч.", "дн.") deliberately sidestep Russian/
  // Kazakh plural-form agreement (1 минута / 2 минуты / 5 минут), the way
  // real news UIs do — spelling every count out correctly would need a
  // full plural-rules table for three units in two languages.
  ru: { justNow: "только что", minute: " мин. назад", hour: " ч. назад", day: " дн. назад" },
  kk: { justNow: "жаңа ғана", minute: " мин. бұрын", hour: " сағ. бұрын", day: " күн бұрын" },
} as const;

export function timeAgo(iso: string, lang: keyof typeof TIME_AGO_UNITS = "en"): string {
  const units = TIME_AGO_UNITS[lang];
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return units.justNow;
  if (minutes < 60) return `${minutes}${units.minute}`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}${units.hour}`;
  const days = Math.floor(hours / 24);
  return `${days}${units.day}`;
}

const BREAKING_NEWS_MAX_AGE_MINUTES = 120;
const BREAKING_NEWS_MIN_IMPACT_SCORE = 60;

/**
 * "Breaking" is a real, deterministic read of data the classifier
 * already produced at ingest time (app/intelligence/news/classifier.py)
 * — recent AND independently scored as significant — never a fabricated
 * or editorial label. Both thresholds are intentionally conservative so
 * this stays rare enough to mean something.
 */
export function isBreakingNews(publishedAt: string, impactScore: number): boolean {
  const ageMinutes = (Date.now() - new Date(publishedAt).getTime()) / 60000;
  return ageMinutes >= 0 && ageMinutes <= BREAKING_NEWS_MAX_AGE_MINUTES && impactScore >= BREAKING_NEWS_MIN_IMPACT_SCORE;
}
