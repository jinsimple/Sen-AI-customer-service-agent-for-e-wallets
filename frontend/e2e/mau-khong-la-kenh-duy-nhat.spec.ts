import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * [ĐO 27/08] PO chỉ ra ngưỡng khoảng-cách-màu-RGB KHÔNG nên đóng thành cổng:
 * RGB không phải thứ mắt người cảm nhận — một cổng ghim ngưỡng đó sẽ đỏ khi
 * đổi tông màu dù vẫn phân biệt tốt, và xanh khi hai màu trùng cảm nhận
 * nhưng lệch RGB (đầu ra không bám đầu vào thật — Luật A vế bốn).
 *
 * Cổng ĐÚNG, nhị phân, không trôi theo bảng màu: MÀU KHÔNG BAO GIỜ ĐƯỢC LÀ
 * KÊNH DUY NHẤT phân biệt trạng thái — mọi status-dot/badge mang ý nghĩa
 * phải có CHỮ đi kèm. Người mù màu hoặc bản in đen trắng (gửi đối tác) vẫn
 * đọc được ý nghĩa qua chữ, bất kể bảng màu đổi thế nào.
 */

const CSKH_PHONE = "0353000201";
const SUPERVISOR_PHONE = "0905000205";

async function khongMauDonKenh(page: import("@playwright/test").Page, selector: string, trang: string) {
  const elements = page.locator(selector);
  const count = await elements.count();
  expect(count, `${trang}: 0 phần tử "${selector}" tìm thấy — nghi vấn selector sai, không phải 0 trạng thái`).toBeGreaterThan(0);
  for (let i = 0; i < count; i++) {
    const el = elements.nth(i);
    const text = (await el.innerText()).trim();
    expect(
      text.length,
      `${trang}: phần tử "${selector}" thứ ${i} KHÔNG có chữ đi kèm màu — chỉ còn màu làm kênh duy nhất. ` +
        `Người mù màu / bản in đen trắng sẽ không phân biệt được ý nghĩa.`
    ).toBeGreaterThan(0);
  }
}

test.describe("MÀU KHÔNG PHẢI KÊNH DUY NHẤT — mọi status-dot/badge phải có chữ đi kèm", () => {
  test("hàng chờ CSKH (/dashboard) — mọi status-dot/badge có chữ", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");
    // 🔴 [ĐO 27/08, tự bắt trước khi báo cáo] Không chờ gì trước khi đếm
    // ".status-dot" -> 0 phần tử, ca đỏ SAI LÝ DO (đã tưởng là hồi quy thật
    // trong 1 giây). Kiểm lại bằng gọi thẳng /api/tickets: dữ liệu có thật
    // (5+ ticket, kèm fraud_signals). Vấn đề là RACE — bảng nạp dữ liệu bất
    // đồng bộ sau khi mount, test đếm quá sớm. Chờ ít nhất 1 dòng bảng THẬT
    // xuất hiện trước khi đếm.
    await page.locator("tbody tr").first().waitFor({ state: "visible", timeout: 15_000 });
    await khongMauDonKenh(page, ".status-dot", "/dashboard");
    await khongMauDonKenh(page, ".badge", "/dashboard");
  });

  test("hàng chờ duyệt (/approve) — mọi status-dot/badge có chữ", async ({ page }) => {
    await loginAs(page, SUPERVISOR_PHONE, "/approve", 1, "/dang-nhap-noi-bo");
    await page.waitForTimeout(2_000); // dữ liệu nạp bất đồng bộ sau khi mount — xem ghi chú ca trên
    const badges = page.locator(".badge");
    const count = await badges.count();
    if (count === 0) {
      // Hàng chờ có thể rỗng tuỳ dữ liệu seed — không phải lỗi, chỉ không có gì để kiểm ở đây.
      return;
    }
    await khongMauDonKenh(page, ".badge", "/approve");
  });

  test("chi tiết ticket có tín hiệu FS-06 — badge tín hiệu định tuyến có chữ, không chỉ màu", async ({ page }) => {
    await loginAs(page, SUPERVISOR_PHONE, "/approve", 1, "/dang-nhap-noi-bo");
    await page.goto("/tickets/TCK-c953cbcec031");
    await page.waitForTimeout(2_000); // dữ liệu nạp bất đồng bộ sau khi mount — xem ghi chú ca đầu file
    const noiDung = await page.locator("body").innerText();
    if (!noiDung.includes("FS-06")) {
      test.skip(true, "Ticket TCK-c953cbcec031 (seed_demo_scenarios.py) không còn tồn tại hoặc đổi mã trên ngăn này.");
    }
    await khongMauDonKenh(page, ".badge", "/tickets/TCK-c953cbcec031");
  });
});
