import { test, expect, type Page } from "@playwright/test";
import { DEMO_PASSWORD } from "./helpers/actors";

/**
 * [ĐO 26/08] PO đảo quyết định trong ngày: sáng nay chốt "nhân viên lỡ vào
 * /login CỨ CHO VÀO" (57b9b7d), chiều nay PO thật CHỐT NGƯỢC LẠI — CHẶN nhân
 * viên đăng nhập ở `/login` ("trang khách chỉ cho khách"). Viết TỪ ĐẶC TẢ
 * này, KHÔNG đọc `src/` (CLAUDE.md §4) — hành vi CHƯA được cài đặt tại thời
 * điểm viết ca này, nên các ca "phải bị từ chối" bên dưới ĐANG ĐỎ trên code
 * hiện tại, ĐÚNG NHƯ KỲ VỌNG — đây là ca-đặc-tả-trước (spec trước, code sau),
 * không phải test hỏng. Xanh trở lại khi tech-lead cài đặt xong việc chặn.
 *
 * 🔴🔴 KHÔNG PHẢI CỔNG BẢO MẬT — chỉ là PHÂN TÁCH TỔ CHỨC (UX/routing). Cả
 * `/login` lẫn `/dang-nhap-noi-bo` gọi CHUNG một endpoint `/api/session`
 * (useLoginForm.ts) — ai gọi thẳng API (curl, Postman, script) vẫn ĐI VÒNG
 * được hoàn toàn, việc chặn ở đây chỉ áp tại tầng TRANG. Đừng đọc tên file
 * này thành "đã có lớp chặn ở API" rồi bớt lớp bảo vệ thật ở nơi khác — thẩm
 * quyền THẬT vẫn nằm ở `contracts/authority-matrix.yaml` + `require_role()`
 * (tests/test_invariants.py), không phải ở đây.
 */

const CUSTOMER_PHONE = "0974000145"; // USR-0145, role=customer
const CSKH_PHONE = "0353000201";
const SUPERVISOR_PHONE = "0905000205";
const PARTNER_ADMIN_PHONE = "0900000001";
const KHONG_TON_TAI_PHONE = "0999999999"; // không có trong dataset — mốc "tài khoản không tồn tại"

async function submitLogin(page: Page, path: string, phone: string, password: string): Promise<{ error: string | null }> {
  await page.goto(path);
  await page.getByPlaceholder("09xx xxx xxx").fill(phone);
  await page.getByPlaceholder("••••••••").fill(password);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  // Chờ MỘT trong hai: điều hướng đi (thành công) hoặc thông báo lỗi hiện ra
  // (thất bại) — không waitForURL cứng, vì ca thất bại không điều hướng đi.
  await page.waitForTimeout(1_500);
  const url = page.url();
  if (!url.includes(path.split("?")[0])) {
    return { error: null }; // đã điều hướng đi -> đăng nhập thành công
  }
  const errorEl = page.locator(".field-error, [class*=error]").first();
  const error = (await errorEl.count()) > 0 ? await errorEl.textContent() : null;
  return { error };
}

test.describe("SEC/ORG — tách cổng /login (khách) vs /dang-nhap-noi-bo (nội bộ), KHÔNG phải lớp bảo mật", () => {
  test("khách đăng nhập ở /login -> vào được bình thường", async ({ page }) => {
    const { error } = await submitLogin(page, "/login", CUSTOMER_PHONE, DEMO_PASSWORD);
    expect(error, "Khách hàng đúng cổng, đúng mật khẩu phải vào được — không được chặn nhầm").toBeNull();
  });

  for (const [vaiTro, phone] of [
    ["CSKH", CSKH_PHONE],
    ["sếp phê duyệt", SUPERVISOR_PHONE],
    ["đối tác ví", PARTNER_ADMIN_PHONE],
  ] as const) {
    test(`${vaiTro} đăng nhập ở /login (SAI cổng) -> bị từ chối, không lập phiên`, async ({ page }) => {
      const { error } = await submitLogin(page, "/login", phone, DEMO_PASSWORD);
      expect(
        error,
        `${vaiTro} (${phone}) đăng nhập đúng mật khẩu nhưng SAI cổng (/login) — phải bị từ chối, ` +
          `không được lập phiên. Đang ĐỎ vì hành vi này CHƯA được cài đặt (PO chốt 26/08, chờ tech-lead).`
      ).not.toBeNull();
    });
  }

  test("khách đăng nhập ở /dang-nhap-noi-bo (SAI cổng) -> bị từ chối", async ({ page }) => {
    const { error } = await submitLogin(page, "/dang-nhap-noi-bo", CUSTOMER_PHONE, DEMO_PASSWORD);
    expect(
      error,
      "Khách hàng đúng mật khẩu nhưng sai cổng (/dang-nhap-noi-bo) — phải bị từ chối. " +
        "Đang ĐỎ vì hành vi này CHƯA được cài đặt."
    ).not.toBeNull();
  });

  test("🔴 CA CHỐNG RÒ RỈ — sai mật khẩu/sai cổng/không tồn tại đều CÙNG MỘT câu lỗi, không lộ vai", async ({
    browser,
  }) => {
    // Luật A — ca đối chứng bắt buộc, và đây là ca QUAN TRỌNG NHẤT của file:
    // thiếu nó, một bản cài đặt "chặn sai cổng" có thể vô tình dùng thông báo
    // lỗi KHÁC với "sai mật khẩu" (vd "Tài khoản này đăng nhập ở cổng khác" so
    // với "Sai mật khẩu") — khi đó, AI CŨNG DÒ ĐƯỢC một số điện thoại là nhân
    // viên hay khách hàng CHỈ BẰNG CÁCH thử đăng nhập sai mật khẩu ở /login,
    // không cần biết mật khẩu thật — rò rỉ nghiêm trọng hơn cả việc chặn nhầm.
    const ngu_canh = [
      { ten: "khách, sai mật khẩu, đúng cổng", path: "/login", phone: CUSTOMER_PHONE, mat_khau: "sai-mat-khau-123" },
      { ten: "sếp, đúng mật khẩu, sai cổng", path: "/login", phone: SUPERVISOR_PHONE, mat_khau: DEMO_PASSWORD },
      { ten: "sếp, sai mật khẩu, sai cổng", path: "/login", phone: SUPERVISOR_PHONE, mat_khau: "sai-mat-khau-123" },
      {
        ten: "khách, đúng mật khẩu, sai cổng (chiều ngược)",
        path: "/dang-nhap-noi-bo",
        phone: CUSTOMER_PHONE,
        mat_khau: DEMO_PASSWORD,
      },
      {
        ten: "số điện thoại không tồn tại",
        path: "/login",
        phone: KHONG_TON_TAI_PHONE,
        mat_khau: "bat-ky-mat-khau",
      },
    ];

    const thongDiep: { ten: string; loi: string | null }[] = [];
    for (const nc of ngu_canh) {
      const context = await browser.newContext();
      const page = await context.newPage();
      try {
        const { error } = await submitLogin(page, nc.path, nc.phone, nc.mat_khau);
        thongDiep.push({ ten: nc.ten, loi: error });
      } finally {
        await context.close();
      }
    }

    for (const t of thongDiep) {
      expect(t.loi, `Ngữ cảnh "${t.ten}" phải bị từ chối (có thông báo lỗi), không được lọt qua`).not.toBeNull();
    }

    const tapHopLoi = new Set(thongDiep.map((t) => t.loi));
    expect(
      tapHopLoi.size,
      `Các ngữ cảnh trên phải trả về Y HỆT một câu lỗi — hiện có ${tapHopLoi.size} câu KHÁC NHAU, ` +
        `nghĩa là có thể dò được vai trò/sự tồn tại của một số điện thoại chỉ bằng câu lỗi trả về, ` +
        `không cần biết mật khẩu thật:\n` +
        thongDiep.map((t) => `  - ${t.ten}: ${JSON.stringify(t.loi)}`).join("\n")
    ).toBe(1);
  });
});
