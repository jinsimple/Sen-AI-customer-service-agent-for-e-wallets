import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * CỔNG GHIM — `ALWAYS_PUBLIC_PATHS` trong `proxy.ts`.
 *
 * Mảng ấy nghĩa là: *"KHÔNG kiểm phiên ở bất kỳ nhánh nào"* — request đi thẳng,
 * không redirect theo chiều nào. [ĐO 27/08, Review soát `abd4908`] bảo vệ DUY
 * NHẤT của nó là TÊN BIẾN + đoạn chú thích ngay trên: không test, không lint
 * rule, không ràng buộc runtime. Người sau đẩy thêm MỘT phần tử — có thể là
 * một path CÓ DỮ LIỆU — và không cổng nào kêu.
 *
 * 🔴 MỤC ĐÍCH KHÔNG PHẢI CHẶN người sau thêm path. Họ vẫn thêm được, và đôi khi
 * đúng là phải thêm. Mục đích là buộc họ **sửa một dòng test tường minh** thay
 * vì đẩy im lặng một phần tử vào một mảng trần. Cùng tinh thần `CONTRACT_VERSION`:
 * vá một chỗ thì cả lớp phải chạm tay.
 *
 * VÌ SAO ĐỌC VĂN BẢN THUẦN, KHÔNG `import`: `ALWAYS_PUBLIC_PATHS` là `const` ở
 * tầng module và KHÔNG được export — không có đường import. Xuất nó ra chỉ để
 * test được là nới bề mặt công khai của `proxy.ts` cho một lý do thuộc về test;
 * đọc văn bản giữ `proxy.ts` nguyên vẹn. (Cùng idiom `ChatClient.pin.test.ts`.)
 *
 * VÌ SAO TEST NÀY KHÔNG THUỘC QA/QC: nó CỐ Ý phản chiếu mã — đó là toàn bộ công
 * dụng của nó. Giao cho vai bị cấm đọc `src/` là phá đúng lý do họ bị cấm.
 * QA/QC đo `/cho-khach-hang` bằng HÀNH VI, ở `frontend/e2e/` — hai nguồn độc lập.
 */

const PROXY_TS = resolve(__dirname, "./proxy.ts");
const KHUON = /const\s+ALWAYS_PUBLIC_PATHS\s*=\s*\[([^\]]*)\]/;

/** Bóc mảng chuỗi từ văn bản nguồn. `null` = không tìm thấy khai báo. */
function bocMang(nguon: string): string[] | null {
  const m = KHUON.exec(nguon);
  if (!m) return null;
  const than = m[1].trim();
  if (than === "") return [];
  return than
    .split(",")
    .map((p) => p.trim().replace(/^["'`]|["'`]$/g, ""))
    .filter((p) => p !== "");
}

describe("proxy.ts — ghim ALWAYS_PUBLIC_PATHS", () => {
  it("chứa ĐÚNG một phần tử, đúng /cho-khach-hang", () => {
    const duoc = bocMang(readFileSync(PROXY_TS, "utf8"));
    expect(
      duoc,
      "Không tìm thấy khai báo `const ALWAYS_PUBLIC_PATHS = [...]` trong proxy.ts. " +
        "Nếu bạn vừa đổi TÊN hoặc DẠNG khai báo, cổng này đã mù — sửa KHUON ở " +
        "trên, đừng xoá test.",
    ).not.toBeNull();

    expect(
      duoc,
      "ALWAYS_PUBLIC_PATHS ĐÃ ĐỔI. Mảng này nghĩa là 'KHÔNG kiểm phiên ở bất kỳ " +
        "nhánh nào' — mỗi phần tử là một đường đi bỏ qua xác thực hoàn toàn.\n" +
        "Thêm/bớt là việc CHÍNH ĐÁNG, nhưng phải CỐ Ý: sửa dòng dưới đây, và ghi " +
        "vào commit vì sao path mới không mang dữ liệu cần bảo vệ.",
    ).toEqual(["/cho-khach-hang"]);
  });

  // ĐỐI CHỨNG — chứng minh cổng KÊU được, không chỉ IM được (Luật A).
  // Thiếu hai ca này, một `bocMang` luôn trả `["/cho-khach-hang"]` vì bất kỳ lý
  // do gì (regex hỏng, đọc nhầm file) vẫn làm ca trên XANH mãi mãi.
  it("ĐỐI CHỨNG: bắt được khi có phần tử thứ hai bị đẩy thêm", () => {
    const gia = `const ALWAYS_PUBLIC_PATHS = ["/cho-khach-hang", "/ho-so-khach"];`;
    expect(bocMang(gia)).toEqual(["/cho-khach-hang", "/ho-so-khach"]);
    expect(bocMang(gia)).not.toEqual(["/cho-khach-hang"]);
  });

  it("ĐỐI CHỨNG: trả null khi khai báo biến mất", () => {
    expect(bocMang(`const MOT_MANG_KHAC = ["/cho-khach-hang"];`)).toBeNull();
  });
});
