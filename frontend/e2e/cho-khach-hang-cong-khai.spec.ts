import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * [ĐO 27/08] `/cho-khach-hang` — trang chống lừa đảo (vector phổ biến nhất
 * tại VN: giả danh tổng đài hỏi mã OTP). Yêu cầu lõi, NGƯỢC với mọi trang
 * công khai khác trong dự án: phải đọc được BẤT KỂ có phiên hay không —
 * không được đá đi theo BẤT KỲ chiều nào, vì khách cần trang này ĐÚNG LÚC
 * đang hoảng và nghi ngờ "Sen có đang lừa mình không".
 *
 * Viết TỪ HÀNH VI (Lead cố ý không mô tả cấu trúc mã) — mọi khẳng định dưới
 * đây đo bằng cách BẤM/GỌI THẬT, không đọc `src/`.
 *
 * Đo thêm câu Lead nhấn mạnh hơn cả bảng ra/vào: trang này là trang công
 * khai DUY NHẤT cố ý hiển thị được khi ĐANG có phiên — có rò dấu vết của
 * phiên đó ra không (tên/SĐT/vai)? Cách đo chắc nhất: SO KHỚP TOÀN VĂN nội
 * dung (text hiển thị + HTML thô) giữa 5 trạng thái (không phiên + 4 vai) —
 * nếu có dù một field nào phân biệt theo phiên, hai bản sẽ LỆCH.
 */

const CUSTOMER_PHONE = "0974000145";
const CSKH_PHONE = "0353000201";
const SUPERVISOR_PHONE = "0905000205";
const PARTNER_ADMIN_PHONE = "0900000001";

// Home mỗi vai — khớp auth-multirole.spec.ts (CUSTOMER/CSKH/SUPERVISOR/PARTNER_ADMIN).
const HOME_THEO_PHONE: Record<string, string> = {
  [CUSTOMER_PHONE]: "/chat",
  [CSKH_PHONE]: "/dashboard",
  [SUPERVISOR_PHONE]: "/approve",
  [PARTNER_ADMIN_PHONE]: "/knowledge",
};

// 🔴 [ĐO 27/08] Tính năng chặn sai cổng ĐÃ LAND — nhân viên phải đăng nhập
// qua /dang-nhap-noi-bo, không còn qua /login (xem đính chính cùng ngày ở
// helpers/actors.ts::loginAs). File này là nơi ĐẦU TIÊN chạm phải, sửa tại
// đây thay vì đoán trước cho 40+ lượt gọi khác trong toàn bộ frontend/e2e/.
const CONG_THEO_PHONE: Record<string, "/login" | "/dang-nhap-noi-bo"> = {
  [CUSTOMER_PHONE]: "/login",
  [CSKH_PHONE]: "/dang-nhap-noi-bo",
  [SUPERVISOR_PHONE]: "/dang-nhap-noi-bo",
  [PARTNER_ADMIN_PHONE]: "/dang-nhap-noi-bo",
};

test.describe("PUBLIC — /cho-khach-hang phải vào được BẤT KỂ trạng thái đăng nhập", () => {
  test("không có phiên -> vào được, không bị đá đi đâu", async ({ page }) => {
    await page.goto("/cho-khach-hang");
    await expect(page).toHaveURL(/\/cho-khach-hang$/);
    await expect(page.getByText("Sen là trợ lý AI")).toBeVisible();
  });

  for (const [vaiTro, phone] of [
    ["khách hàng", CUSTOMER_PHONE],
    ["CSKH", CSKH_PHONE],
    ["sếp phê duyệt", SUPERVISOR_PHONE],
    ["đối tác ví", PARTNER_ADMIN_PHONE],
  ] as const) {
    test(`đang đăng nhập vai ${vaiTro} -> vẫn vào được /cho-khach-hang, không bị đá đi`, async ({ page }) => {
      await loginAs(page, phone, HOME_THEO_PHONE[phone], 1, CONG_THEO_PHONE[phone]);
      await page.goto("/cho-khach-hang");
      await expect(page).toHaveURL(/\/cho-khach-hang$/);
      await expect(page.getByText("Sen là trợ lý AI")).toBeVisible();
    });
  }

  test("🔴 CA CHÍNH — nội dung /cho-khach-hang GIỐNG HỆT nhau dù không phiên hay đăng nhập vai bất kỳ (không rò dấu vết phiên)", async ({
    browser,
  }) => {
    async function noiDung(phone: string | null): Promise<{ text: string; html: string }> {
      const context = await browser.newContext();
      const page = await context.newPage();
      try {
        if (phone) {
          await loginAs(page, phone, HOME_THEO_PHONE[phone], 1, CONG_THEO_PHONE[phone]);
        }
        await page.goto("/cho-khach-hang");
        const text = await page.locator("body").innerText();
        const html = await page.content();
        return { text, html };
      } finally {
        await context.close();
      }
    }

    const khongPhien = await noiDung(null);
    for (const [vaiTro, phone] of [
      ["khách hàng", CUSTOMER_PHONE],
      ["CSKH", CSKH_PHONE],
      ["sếp phê duyệt", SUPERVISOR_PHONE],
      ["đối tác ví", PARTNER_ADMIN_PHONE],
    ] as const) {
      const cua = await noiDung(phone);
      expect(
        cua.text,
        `🔴 RÒ DẤU VẾT PHIÊN: nội dung hiển thị /cho-khach-hang khi đăng nhập vai ${vaiTro} ` +
          `KHÁC với lúc không có phiên — trang công khai duy nhất cố ý hiển thị được khi có phiên ` +
          `không được để lộ bất kỳ dấu vết nào (tên/SĐT/vai) của người đang đăng nhập.`
      ).toBe(khongPhien.text);
      expect(
        cua.html,
        `🔴 RÒ DẤU VẾT PHIÊN TRONG HTML THÔ (có thể ẩn bằng CSS nhưng vẫn đọc được qua view-source) ` +
          `khi đăng nhập vai ${vaiTro} — khác lúc không có phiên.`
      ).toBe(khongPhien.html);
    }
  });
});

test.describe("PUBLIC — không hồi quy: các cổng khác vẫn phải chặn đúng như trước", () => {
  test("không có phiên -> /dashboard vẫn đá về đăng nhập (KHÔNG lây tính công khai sang trang khác)", async ({
    page,
  }) => {
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });

  test("CSKH -> /approve vẫn bị chặn như trước (KHÔNG lây tính công khai)", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");
    await page.goto("/approve");
    await expect(page).not.toHaveURL(/\/approve$/);
  });

  for (const bienThe of [
    "/cho-khach-hangXYZ",
    "/cho-khach-hang-abc",
    "/cho-khach-hangs",
    "/Cho-Khach-Hang",
  ]) {
    test(`tên gần giống "${bienThe}" -> KHÔNG được lọt qua như route thật`, async ({ page }) => {
      await page.goto(bienThe);
      await expect(page).not.toHaveURL(new RegExp(`${bienThe}$`));
      // Không assert cứng "phải về /login" — chỉ cần chắc chắn KHÔNG dừng lại
      // ở coi như route công khai thật (không hiện nội dung trang chống lừa đảo).
      await expect(page.getByText("Sen là trợ lý AI")).not.toBeVisible();
    });
  }
});
