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
  // P3-1: quá 48 giờ thì đọc theo NGÀY. "còn 712h44p" bắt người trực tự chia
  // nhẩm mới biết là gần một tháng — đúng lúc họ đang quét nhanh hàng chờ.
  const label =
    hours >= 48 ? `${Math.floor(hours / 24)} ngày` : hours > 0 ? `${hours}h${minutes}p` : `${minutes}p`;
  return { label: overdue ? `quá hạn ${label}` : `còn ${label}`, overdue };
}
