import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * CỔNG GHIM — GĐ2.5, Quyết định B (docs/giao-viec/2026-08-19-gd25-va-finding-ab-otp.md,
 * commit 32751c2). ChatClient.tsx nhận diện OTP-hết-tươi bằng cách khớp
 * CHÍNH XÁC hai hằng số backend TA SỞ HỮU (KHÁC hẳn khớp thân lỗi nhà cung
 * cấp — thứ đã cấm ở GĐ3): backend đóng băng đợt này nên không có đường đọc
 * chung một nguồn, client phải giữ BẢN SAO. Một bản sao không cổng canh sẽ
 * lệch IM LẶNG khi ai đó đổi câu chữ/con số phía backend.
 *
 * Đọc CẢ HAI file như VĂN BẢN THUẦN (regex trên nội dung, KHÔNG `import` từ
 * `src/`) — đây là điều làm cổng này không đụng vách cách ly tester/`src/`
 * (CLAUDE.md §4): nó không thực thi mã Python, không chạy app, chỉ so hai
 * chuỗi/hai con số nằm trong hai file dưới quản lý phiên bản.
 *
 * Nợ có hạn, có chuyến (khai trong Quyết định B): khi backend GĐ3 gỡ băng
 * (đằng nào cũng gỡ cho bể model xoay), thêm field `"loai":"otp_het_tuoi"`
 * vào `_OTP_EXPIRED_ERROR`, client chuyển sang đọc field đó — CỔNG ② THÁO BỎ
 * khi đó. Cổng ① (ngưỡng phút) không phụ thuộc việc đó, vẫn còn.
 */

const REPO_ROOT = resolve(__dirname, "../../../../..");
const CONFIG_PY = resolve(REPO_ROOT, "src/config.py");
const CUSTOMER_TOOLS_PY = resolve(REPO_ROOT, "src/agents/tools/customer_tools.py");
const SESSION_SERVER_TS = resolve(__dirname, "../../../lib/session-server.ts");
const CHAT_CLIENT_TSX = resolve(__dirname, "./ChatClient.tsx");

// Định giá TỐI GIẢN cho `"12 * 60"`/`"720"` — CHỈ số nguyên, `*`, `+`, khoảng
// trắng. Đủ cho hai file đang khai (số phút), không đủ và KHÔNG ĐỊNH đủ cho
// biểu thức bất kỳ — ném lỗi rõ ràng thay vì âm thầm tính sai nếu ai đó viết
// một dạng khác (vd trừ, chia) mà cổng chưa lường.
function tinhBieuThucSo(bieuThuc: string): number {
  const sach = bieuThuc.trim();
  if (!/^\d+(\s*[*+]\s*\d+)*$/.test(sach)) {
    throw new Error(
      `Cổng ghim không định giá được biểu thức "${bieuThuc}" — chỉ hỗ trợ số nguyên + '*'/'+'. ` +
        `Cập nhật tinhBieuThucSo() nếu hằng số backend đổi sang dạng khác.`
    );
  }
  return sach.split("+").reduce(
    (tongSo, hang) => tongSo + hang.split("*").reduce((tich, so) => tich * Number(so.trim()), 1),
    0
  );
}

function docTrich(duongDan: string, mau: RegExp, tenNgan: string): string {
  const noiDung = readFileSync(duongDan, "utf8");
  const m = mau.exec(noiDung);
  if (!m) {
    throw new Error(
      `Cổng ghim KHÔNG đọc được "${tenNgan}" từ ${duongDan} — mẫu regex không khớp gì cả. ` +
        `Đây là "KHÔNG ĐO ĐƯỢC", không phải "khớp"/"lệch" — dừng ở đây, đừng đoán tiếp.`
    );
  }
  return m[1];
}

describe("cổng ghim GĐ2.5 — bản sao hằng số OTP frontend/backend", () => {
  it("① OTP_VIEW_MAX_MINUTES: session-server.ts PHẢI khớp src/config.py", () => {
    const backend = docTrich(CONFIG_PY, /^OTP_VIEW_MAX_MINUTES\s*=\s*(.+)$/m, "OTP_VIEW_MAX_MINUTES (backend)");
    const frontend = docTrich(
      SESSION_SERVER_TS,
      /const OTP_VIEW_MAX_MINUTES\s*=\s*(.+);/,
      "OTP_VIEW_MAX_MINUTES (frontend)"
    );
    // So GIÁ TRỊ, không so văn bản: "12 * 60" và "720" phải được coi là bằng
    // nhau — backend/frontend không bắt buộc viết cùng một kiểu biểu thức.
    // Định giá bằng tay (KHÔNG `eval`/`Function`) — chuỗi tuy là hằng số nội
    // bộ ta viết ra, nhưng một cổng ghim không nên cần biện minh cho việc
    // thực thi mã tuỳ ý mới đọc được một con số.
    expect(tinhBieuThucSo(frontend)).toBe(tinhBieuThucSo(backend));
  });

  it("② _OTP_EXPIRED_ERROR.message: ChatClient.tsx PHẢI khớp customer_tools.py", () => {
    const backend = docTrich(
      CUSTOMER_TOOLS_PY,
      /_OTP_EXPIRED_ERROR\s*=\s*\{[^}]*?"message":\s*"((?:[^"\\]|\\.)*)"/,
      "_OTP_EXPIRED_ERROR.message (backend)"
    );
    const frontend = docTrich(
      CHAT_CLIENT_TSX,
      /const OTP_EXPIRED_MESSAGE\s*=\s*\n?\s*"((?:[^"\\]|\\.)*)"/,
      "OTP_EXPIRED_MESSAGE (frontend)"
    );
    expect(frontend).toBe(backend);
  });
});
