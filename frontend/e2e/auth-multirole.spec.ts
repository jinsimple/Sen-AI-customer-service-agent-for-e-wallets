import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, unlockTxnRail } from "./helpers/actors";
import { forgeAccessTokenExpiry, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * AUTH5-HARD-01 (đợt nâng cấp Auth Flow, 2026-08-12) — kịch bản khó nhất cho
 * LUỒNG ĐĂNG NHẬP: cả 4 role (customer/cskh/supervisor/partner_admin) đăng
 * nhập ĐỒNG THỜI qua UI thật (stress rate-limit khoá theo phone — AUTH5-08 —
 * dưới tải đa-actor thật, không phải tuần tự từng role như các spec khác),
 * chặn chéo role qua URL (proxy.ts, không chỉ ẩn UI), access_token tự làm
 * mới GIỮA phiên không cần chờ 15 phút thật (AUTH5-02), refresh_token bị
 * ĐÁNH CẮP và tái sử dụng bị PHÁT HIỆN (AUTH5-03, family bị thu hồi — phần
 * khó nhất, chạy qua ĐÚNG chuỗi browser → proxy.ts → backend thật, không chỉ
 * pytest gọi thẳng API), và đăng xuất thu hồi refresh_token NGAY (AUTH5-06).
 *
 * Khác `tests/test_api/test_auth_jwt_refresh.py` (đã test đủ các case này ở
 * tầng HTTP thuần) — bài này xác nhận CHÍNH proxy.ts (điểm duy nhất áp dụng
 * logic refresh cho ~30 route BFF, xem ghi chú trong file đó) thật sự gọi
 * đúng, đúng lúc, và cookie trình duyệt thật sự được cập nhật.
 */

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";

const CUSTOMER = { phone: "0387000001", home: "/chat" };
const CSKH = { phone: "0353000201", home: "/dashboard" };
const SUPERVISOR = { phone: "0905000205", home: "/approve" };
const PARTNER_ADMIN = { phone: "0900000001", home: "/knowledge" };

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} thật — chưa đăng nhập?`);
  return session;
}

test.describe("AUTH5-HARD-01 — luồng đăng nhập, cả 4 role cùng lúc (khó nhất)", () => {
  test("4 role đăng nhập đồng thời → chặn chéo qua URL → tự làm mới access token giữa phiên → refresh-token bị đánh cắp bị phát hiện → đăng xuất thu hồi ngay", async ({
    browser,
  }) => {
    test.setTimeout(120_000);

    const actors = [CUSTOMER, CSKH, SUPERVISOR, PARTNER_ADMIN];
    const contexts = await Promise.all(actors.map(() => browser.newContext()));
    const pages = await Promise.all(contexts.map((c) => c.newPage()));
    const [customerPage, cskhPage, supervisorPage, partnerPage] = pages;

    try {
      // --- 1) Đăng nhập ĐỒNG THỜI cả 4 role (Promise.all — 4 request HTTP
      // thật đua nhau ở backend). 4 phone KHÁC nhau, CÙNG 1 IP nguồn (máy
      // chạy Playwright) — đúng kịch bản AUTH5-08 đã vá (khoá theo phone,
      // không còn khoá theo IP): nếu bug cũ còn, các login này dễ tranh chấp
      // ngưỡng chung dù không ai sai gì.
      await Promise.all(actors.map((a, i) => loginAs(pages[i], a.phone, a.home)));

      // --- 2) Chặn chéo role qua URL (proxy.ts) — mỗi role cố vào ĐÚNG 1
      // trang CHỈ role KHÁC được phép, phải bị đá về nhà CHÍNH MÌNH (không
      // phải /login — đã đăng nhập hợp lệ, chỉ sai role cho trang đó).
      await customerPage.goto("/dashboard"); // cskh-only
      await customerPage.waitForURL("**/chat**", { timeout: 10_000 });
      await cskhPage.goto("/approve"); // supervisor-only
      await cskhPage.waitForURL("**/dashboard**", { timeout: 10_000 });
      await supervisorPage.goto("/knowledge"); // partner_admin-only
      await supervisorPage.waitForURL("**/approve**", { timeout: 10_000 });
      await partnerPage.goto("/chat"); // customer-only
      await partnerPage.waitForURL("**/knowledge**", { timeout: 10_000 });

      // --- 3) Khách: access_token "hết hạn" GIỮA phiên (không chờ 15 phút
      // thật) — proxy.ts (AUTH5-02) phải tự gọi /auth/refresh TRƯỚC khi
      // trang render, khách không thấy gì bất thường (không rơi về /login,
      // rail giao dịch vẫn load được — chứng minh access_token MỚI đã hoạt
      // động thật, không chỉ "không lỗi").
      //
      // 🔴 [ĐO] GĐ2 (19/08, Lead): unlockTxnRail() PHẢI chạy TRƯỚC bước giả
      // mạo hết hạn bên dưới, KHÔNG được chèn sau reload. Ca này khẳng định
      // "rail vẫn load được = access_token MỚI đã hoạt động thật" — nếu mở
      // rail SAU KHI đã giả hết hạn+reload, chính thao tác mở rail sẽ tự sửa
      // trạng thái đang được quan sát, biến bằng chứng thành hằng-đúng (xanh
      // dù refresh có chạy hay không). Mở TRƯỚC, bằng phiên còn hợp lệ, để
      // .txn-item ở dòng dưới chỉ còn MỘT lời giải thích: refresh đã chạy.
      await unlockTxnRail(customerPage);

      const customerSession = await readSessionCookie(contexts[0]);
      const expiredCustomer = forgeAccessTokenExpiry(customerSession, -30); // hết hạn 30s trước
      await setForgedSessionCookie(contexts[0], expiredCustomer);
      await customerPage.reload();
      await expect(customerPage.locator(".txn-item").first()).toBeVisible({ timeout: 15_000 });
      expect(customerPage.url()).toContain("/chat");

      // --- 4) Sếp: mô phỏng refresh_token bị ĐÁNH CẮP — "kẻ tấn công" gọi
      // THẲNG backend rotate trước (không qua trình duyệt hợp pháp), có
      // được access_token/refresh_token MỚI hợp lệ từ token bị lộ.
      const supervisorSession = await readSessionCookie(contexts[2]);
      const attackerRotate = await supervisorPage.request.post(`${BACKEND_URL}/auth/refresh`, {
        data: { refresh_token: supervisorSession.refresh_token },
      });
      expect(attackerRotate.ok()).toBe(true);

      // Trình duyệt HỢP PHÁP (vẫn cầm refresh_token GỐC, không hề biết vừa
      // bị đánh cắp) tự làm mới khi access_token hết hạn -> BỊ TỪ CHỐI (dùng
      // lại refresh_token đã rotate = reuse detected -> thu hồi CẢ family,
      // xem src/auth.py::rotate_refresh_token) — cầm đúng refresh_token gốc
      // KHÔNG còn nghĩa là hợp lệ nữa. proxy.ts phải xoá cookie chết và đá
      // về /login, không kẹt ở trang trắng/lỗi.
      const expiredSupervisor = forgeAccessTokenExpiry(supervisorSession, -30);
      await setForgedSessionCookie(contexts[2], expiredSupervisor);
      await supervisorPage.reload();
      await supervisorPage.waitForURL("**/login**", { timeout: 15_000 });

      // --- 5) CSKH: đăng xuất qua UI -> refresh_token bị thu hồi NGAY, không
      // chờ hết hạn tự nhiên (AUTH5-06). Kiểm THẬT bằng cách gọi thẳng
      // backend bằng CHÍNH refresh_token cũ SAU KHI đã đăng xuất.
      const cskhSession = await readSessionCookie(contexts[1]);
      await cskhPage.getByRole("button", { name: "Đăng xuất" }).click();
      await cskhPage.waitForURL("**/login**", { timeout: 10_000 });
      const reuseAfterLogout = await cskhPage.request.post(`${BACKEND_URL}/auth/refresh`, {
        data: { refresh_token: cskhSession.refresh_token },
      });
      expect(reuseAfterLogout.status()).toBe(401);

      // --- 6) Đối tác ví: sau tất cả biến động trên (login đồng thời, 3
      // role khác vừa refresh/theft/logout), phiên của partner_admin — vốn
      // KHÔNG đụng tới gì ở các bước trên — vẫn phải còn nguyên vẹn, không
      // bị ảnh hưởng chéo bởi bất kỳ thao tác nào của 3 actor kia.
      await partnerPage.goto("/knowledge");
      await expect(partnerPage).toHaveURL(/\/knowledge/);
      await expect(partnerPage.getByRole("button", { name: "Đăng xuất" })).toBeVisible({ timeout: 10_000 });
    } finally {
      await Promise.all(contexts.map((c) => c.close()));
    }
  });
});
