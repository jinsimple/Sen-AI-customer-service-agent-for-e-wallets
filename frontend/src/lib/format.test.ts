import { describe, expect, it, vi } from "vitest";
import { formatDateTime, formatMoney, formatSlaRemaining } from "./format";

// FIN05-StressTest-Plan-v4 F4-03 — helper thuần dùng chung nhiều nơi
// (dashboard/ticket-detail/report), test đầu tiên thiết lập convention
// Vitest cho dự án (xem F4-04 cho ví dụ với hook, F4-05 cho component).

describe("formatMoney", () => {
  it("thêm 'đ' và dấu phân cách nghìn kiểu vi-VN", () => {
    expect(formatMoney(1_000_000)).toBe("1.000.000đ");
  });

  it("số 0 vẫn hiện đúng, không rỗng", () => {
    expect(formatMoney(0)).toBe("0đ");
  });
});

describe("formatDateTime", () => {
  it("format đúng HH:mm DD-MM theo giờ Việt Nam (UTC+7)", () => {
    const result = formatDateTime("2026-08-12T09:05:00Z");
    // 09:05 UTC = 16:05 giờ VN (UTC+7), cùng ngày 12-08.
    expect(result).toBe("16:05 12-08");
  });
});

describe("formatSlaRemaining", () => {
  it("hạn còn trong tương lai -> overdue=false, nhãn 'còn'", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-12T00:00:00Z"));
    const { label, overdue } = formatSlaRemaining("2026-08-12T05:30:00Z");
    expect(overdue).toBe(false);
    expect(label).toBe("còn 5h30p");
    vi.useRealTimers();
  });

  it("hạn đã qua -> overdue=true, nhãn 'quá hạn'", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-12T10:00:00Z"));
    const { label, overdue } = formatSlaRemaining("2026-08-12T08:00:00Z");
    expect(overdue).toBe(true);
    expect(label).toBe("quá hạn 2h0p");
    vi.useRealTimers();
  });

  it("dưới 1 giờ -> chỉ hiện phút, không hiện '0h'", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-08-12T00:00:00Z"));
    const { label } = formatSlaRemaining("2026-08-12T00:45:00Z");
    expect(label).toBe("còn 45p");
    vi.useRealTimers();
  });
});
