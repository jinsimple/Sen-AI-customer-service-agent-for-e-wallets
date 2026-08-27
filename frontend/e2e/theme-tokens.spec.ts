import { test, expect } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

/**
 * Cổng canh CẤU TRÚC ba khối màu trong `globals.css` — KHÔNG canh giá trị
 * màu nào đẹp/đúng, chỉ canh "có quên một chỗ không". Đúc theo yêu cầu PO
 * 25/08 (trước khi Coder đổi toàn bộ bộ màu/phông sang style tối giản):
 * đổi màu chạm BA khối `:root` / `:root[data-theme="dark"]` /
 * `@media (prefers-color-scheme: dark)`; sửa hai quên một → người để chế
 * độ HỆ THỐNG (mặc định đa số máy) thấy chữ theme này trên nền theme kia —
 * không test nào đỏ, không log nào kêu, vì máy đo lại thường không ở đúng
 * chế độ hệ thống gây lỗi.
 *
 * ## Bất biến THẬT — không phải "ba khối giống hệt nhau"
 *
 * `:root` là khối NỀN, giữ TOÀN BỘ token (kể cả token không đổi theo theme
 * như `--fs-*`, `--navy`, `--radius*`, `--lh-*`) — các token đó CỐ Ý chỉ
 * sống ở đây, không có gì "quên" cả nếu chúng vắng mặt ở hai khối dark.
 *
 * Hai khối **dark** (`:root[data-theme="dark"]` và khối bên trong
 * `@media (prefers-color-scheme: dark)`) tồn tại để làm ĐÚNG MỘT việc:
 * ĐẢO cùng một tập token khi vào chế độ tối, qua HAI đường kích hoạt khác
 * nhau (bấm nút đổi theme vs theo hệ thống). Chúng PHẢI định nghĩa **CÙNG
 * MỘT TẬP tên biến** — lệch tập là đúng hình dạng lỗi "sửa hai quên một".
 * Mỗi biến trong hai khối dark cũng PHẢI đã tồn tại ở `:root` (không có gì
 * để "đảo" nếu chưa có giá trị nền).
 */

const CSS_PATH = path.resolve(__dirname, "../src/app/globals.css");

function trichBienTrongKhoi(cssText: string, batDauKhoi: RegExp): Set<string> {
  const m = batDauKhoi.exec(cssText);
  if (!m) return new Set();
  // Tìm dấu `{` mở khối ngay sau vị trí khớp, rồi đếm ngoặc để tìm đúng `}` đóng —
  // globals.css có khối lồng nhau (@media > :root:not(...)), không thể cắt bằng
  // regex "đến dấu } đầu tiên".
  let i = m.index + m[0].length;
  while (cssText[i] !== "{") i++;
  let depth = 0;
  const batDauNoiDung = i;
  for (; i < cssText.length; i++) {
    if (cssText[i] === "{") depth++;
    else if (cssText[i] === "}") {
      depth--;
      if (depth === 0) break;
    }
  }
  const noiDungKhoi = cssText.slice(batDauNoiDung + 1, i);
  const bien = new Set<string>();
  for (const dong of noiDungKhoi.matchAll(/(--[a-zA-Z0-9-]+)\s*:/g)) {
    bien.add(dong[1]);
  }
  return bien;
}

function trichBaKhoi(cssText: string) {
  // 🔴 KHÔNG đưa `\{` vào cuối các regex này — `trichBienTrongKhoi` tự tìm
  // dấu `{` NGAY SAU vị trí khớp để bắt đầu đếm ngoặc. Nếu regex đã "ăn"
  // luôn `{`, hàm sẽ đi tìm dấu `{` KẾ TIẾP (ở khối xa hơn) và đếm nhầm nội
  // dung khối đó — lỗi thật đã bắt được lúc viết ca đối chứng: bài học tại
  // đây, không lặp lại (Luật P).
  const nen = trichBienTrongKhoi(cssText, /:root(?!\[|:not)/);
  const darkAttribute = trichBienTrongKhoi(cssText, /:root\[data-theme="dark"\]/);
  const darkMedia = trichBienTrongKhoi(cssText, /@media \(prefers-color-scheme: dark\)/);
  return { nen, darkAttribute, darkMedia };
}

function soSanhTap(a: Set<string>, b: Set<string>) {
  const chiAcoA = [...a].filter((x) => !b.has(x)).sort();
  const chiCoB = [...b].filter((x) => !a.has(x)).sort();
  return { chiAcoA, chiCoB };
}

test.describe("Cổng cấu trúc token màu — globals.css", () => {
  test("hai khối dark (data-theme + prefers-color-scheme) định nghĩa ĐÚNG CÙNG một tập biến", () => {
    const cssText = fs.readFileSync(CSS_PATH, "utf-8");
    const { darkAttribute, darkMedia } = trichBaKhoi(cssText);
    expect(darkAttribute.size, "Không trích được biến nào từ khối :root[data-theme=\"dark\"] — kiểm lại regex/khối có còn đúng tên không.").toBeGreaterThan(0);
    expect(darkMedia.size, "Không trích được biến nào từ khối @media (prefers-color-scheme: dark) — kiểm lại regex/khối có còn đúng tên không.").toBeGreaterThan(0);

    const { chiAcoA: chiCoODataTheme, chiCoB: chiCoOPrefersColor } = soSanhTap(darkAttribute, darkMedia);
    expect(
      { chiCoODataTheme, chiCoOPrefersColor },
      `LỆCH TẬP BIẾN giữa hai khối dark — đúng hình dạng "sửa hai quên một":\n` +
        `  chỉ có ở :root[data-theme="dark"], THIẾU ở @media prefers-color-scheme: ${chiCoODataTheme.join(", ") || "(không)"}\n` +
        `  chỉ có ở @media prefers-color-scheme, THIẾU ở :root[data-theme="dark"]: ${chiCoOPrefersColor.join(", ") || "(không)"}\n` +
        `Người để chế độ HỆ THỐNG sẽ thấy chữ theme này trên nền theme kia ở đúng biến bị thiếu.`
    ).toEqual({ chiCoODataTheme: [], chiCoOPrefersColor: [] });
  });

  test("mọi biến trong hai khối dark đều đã tồn tại ở :root (nền)", () => {
    const cssText = fs.readFileSync(CSS_PATH, "utf-8");
    const { nen, darkAttribute, darkMedia } = trichBaKhoi(cssText);
    const laMoTrongDark = [...darkAttribute, ...darkMedia].filter((b) => !nen.has(b));
    expect(
      [...new Set(laMoTrongDark)],
      `Biến xuất hiện trong khối dark nhưng KHÔNG có ở :root (nền) — không có gì để "đảo", có thể là tên gõ sai/token đã đổi tên ở một bên: ${laMoTrongDark.join(", ")}`
    ).toEqual([]);
  });
});

test.describe("Ca đối chứng (Luật A) — chứng minh cổng THẬT SỰ kêu, chạy trên văn bản CSS giả", () => {
  test("bắt được khi khối data-theme=dark THIẾU một biến so với khối prefers-color-scheme", () => {
    const gia = `
      :root{ --bg:#fff; --text:#000; --danger:#c00; }
      :root[data-theme="dark"]{ --bg:#000; --text:#fff; }
      @media (prefers-color-scheme: dark){
        :root:not([data-theme="light"]){ --bg:#000; --text:#fff; --danger:#f66; }
      }
    `;
    const { darkAttribute, darkMedia } = trichBaKhoi(gia);
    const { chiAcoA, chiCoB } = soSanhTap(darkAttribute, darkMedia);
    expect(chiCoB, "Phải bắt được --danger THIẾU ở khối data-theme=dark").toEqual(["--danger"]);
    expect(chiAcoA).toEqual([]);
  });

  test("bắt được khi một biến trong khối dark không hề tồn tại ở :root", () => {
    const gia = `
      :root{ --bg:#fff; }
      :root[data-theme="dark"]{ --bg:#000; --mau-danh-thieu:#f00; }
      @media (prefers-color-scheme: dark){
        :root:not([data-theme="light"]){ --bg:#000; --mau-danh-thieu:#f00; }
      }
    `;
    const { nen, darkAttribute, darkMedia } = trichBaKhoi(gia);
    const laMoTrongDark = [...darkAttribute, ...darkMedia].filter((b) => !nen.has(b));
    expect([...new Set(laMoTrongDark)]).toEqual(["--mau-danh-thieu"]);
  });

  test("KHÔNG báo oan khi :root có nhiều token hơn hai khối dark (token không đổi theo theme — đúng thiết kế hiện tại)", () => {
    const gia = `
      :root{ --bg:#fff; --text:#000; --fs-16:16px; --navy:#4C1D95; --radius:12px; }
      :root[data-theme="dark"]{ --bg:#000; --text:#fff; }
      @media (prefers-color-scheme: dark){
        :root:not([data-theme="light"]){ --bg:#000; --text:#fff; }
      }
    `;
    const { nen, darkAttribute, darkMedia } = trichBaKhoi(gia);
    const { chiAcoA, chiCoB } = soSanhTap(darkAttribute, darkMedia);
    expect(chiAcoA).toEqual([]);
    expect(chiCoB).toEqual([]);
    const laMoTrongDark = [...darkAttribute, ...darkMedia].filter((b) => !nen.has(b));
    expect(laMoTrongDark, "--fs-16/--navy/--radius chỉ ở :root là ĐÚNG THIẾT KẾ, không được báo lỗi").toEqual([]);
  });
});
