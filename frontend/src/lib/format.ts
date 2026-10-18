import type { Lang } from "./i18n/core";

// `lang` defaults to "vi" so existing callers and unit tests keep their meaning; components pass the
// current UI language from `useI18n()` / `getT()`.

export function formatDateTime(iso: string, lang: Lang = "vi"): string {
  const d = new Date(iso);
  return d.toLocaleString(lang === "en" ? "en-GB" : "vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMoney(amount: number, lang: Lang = "vi"): string {
  // The currency is always VND; only the digit grouping follows the UI language.
  return lang === "en" ? `${amount.toLocaleString("en-US")} ₫` : amount.toLocaleString("vi-VN") + "đ";
}

export function formatSlaRemaining(iso: string, lang: Lang = "vi"): { label: string; overdue: boolean } {
  const diffMs = new Date(iso).getTime() - Date.now();
  const overdue = diffMs < 0;
  const abs = Math.abs(diffMs);
  const hours = Math.floor(abs / 3_600_000);
  const minutes = Math.floor((abs % 3_600_000) / 60_000);
  // P3-1: past 48 hours, read in DAYS. "712h44m left" forces the on-call agent to do mental
  // division to realise it's almost a month — right when they are skimming the queue.
  if (lang === "en") {
    const label =
      hours >= 48 ? `${Math.floor(hours / 24)} days` : hours > 0 ? `${hours}h${minutes}m` : `${minutes}m`;
    return { label: overdue ? `overdue ${label}` : `${label} left`, overdue };
  }
  const label =
    hours >= 48 ? `${Math.floor(hours / 24)} ngày` : hours > 0 ? `${hours}h${minutes}p` : `${minutes}p`;
  return { label: overdue ? `quá hạn ${label}` : `còn ${label}`, overdue };
}
