export function formatDateTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatMoney(amount: number): string {
  return amount.toLocaleString("vi-VN") + "đ";
}

export function formatSlaRemaining(iso: string): { label: string; overdue: boolean } {
  const diffMs = new Date(iso).getTime() - Date.now();
  const overdue = diffMs < 0;
  const abs = Math.abs(diffMs);
  const hours = Math.floor(abs / 3_600_000);
  const minutes = Math.floor((abs % 3_600_000) / 60_000);
  const label = hours > 0 ? `${hours}h${minutes}p` : `${minutes}p`;
  return { label: overdue ? `quá hạn ${label}` : `còn ${label}`, overdue };
}
