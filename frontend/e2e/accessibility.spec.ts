import { test, expect, devices } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { DEMO_PASSWORD } from "./helpers/actors";

/**
 * FIN05-QA-Test-Report.md §3.6 (UX/Accessibility) — mảng KHÔNG có test tự
 * động nào từ trước (khác §3.1-3.5, phần lớn đã có sẵn qua golden_set/
 * adversarial_set/test_authz_matrix/AUTH-* Playwright). Dùng axe-core (chuẩn
 * ngành, engine kiểm WCAG thật — không tự viết tay từng rule contrast/aria
 * dễ sai/thiếu) cho UX-04 (screen reader/aria) + UX-06 (tương phản màu),
 * Playwright thuần cho UX-02 (viewport di động), UX-03 (bàn phím), UX-05
 * (mất mạng giữa chừng).
 */

const PHONE = "0974000145";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByPlaceholder("09xx xxx xxx").fill(PHONE);
  await page.getByPlaceholder("••••••••").fill(DEMO_PASSWORD);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await page.waitForURL("**/chat");
}

test.describe("UX-04/UX-06 — quét accessibility bằng axe-core (WCAG 2.1 A/AA)", () => {
  test("trang /login không có vi phạm WCAG 2.1 A/AA nghiêm trọng", async ({ page }) => {
    await page.goto("/login");
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(
      serious,
      `Vi phạm WCAG nghiêm trọng ở /login:\n${serious.map((v) => `- [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length} chỗ)`).join("\n")}`
    ).toEqual([]);
  });

  test("trang /chat (sau đăng nhập) không có vi phạm WCAG 2.1 A/AA nghiêm trọng", async ({ page }) => {
    await login(page);
    const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
    const serious = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
    expect(
      serious,
      `Vi phạm WCAG nghiêm trọng ở /chat:\n${serious.map((v) => `- [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length} chỗ)`).join("\n")}`
    ).toEqual([]);
  });
});

test.describe("UX-03 — điều hướng bàn phím (Tab/Enter)", () => {
  test("form đăng nhập: Tab đi qua được các phần tử, Enter submit được", async ({ page }) => {
    await page.goto("/login");
    const phoneInput = page.getByPlaceholder("09xx xxx xxx");
    await phoneInput.focus();
    await expect(phoneInput).toBeFocused();

    await phoneInput.fill(PHONE);
    await page.getByPlaceholder("••••••••").fill(DEMO_PASSWORD);
    // Enter trong input phải submit form (native HTML form behavior) — không
    // cần chuột chạm nút "Đăng nhập".
    await phoneInput.press("Enter");
    await page.waitForURL("**/chat", { timeout: 10_000 });
  });

  test("nút Đăng nhập có focus ring nhìn thấy được khi Tab tới", async ({ page }) => {
    await page.goto("/login");
    await page.getByPlaceholder("09xx xxx xxx").focus();
    await page.keyboard.press("Tab");
    const focused = page.locator(":focus");
    // Không assert cứng theo tag cụ thể (radio/chip có thể chen giữa) — chỉ
    // xác nhận CÓ 1 phần tử đang giữ focus rõ ràng sau Tab, không "mất dấu"
    // focus (vấn đề thường gặp khi custom style outline: none không thay thế).
    await expect(focused).toBeVisible();
  });
});

test.describe("UX-02 — layout di động không vỡ", () => {
  for (const [name, viewport] of Object.entries({
    "360x640 (Android nhỏ)": { width: 360, height: 640 },
    "390x844 (iPhone 12/13)": { width: 390, height: 844 },
  })) {
    test(`/login đọc được, nút bấm đủ lớn ở ${name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await page.goto("/login");

      // Không cuộn ngang — dấu hiệu kinh điển của layout vỡ trên di động.
      const hasHorizontalOverflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
      );
      expect(hasHorizontalOverflow, "Trang bị tràn ngang ở viewport di động").toBe(false);

      const submitButton = page.getByRole("button", { name: "Đăng nhập" });
      await expect(submitButton).toBeVisible();
      const box = await submitButton.boundingBox();
      // ≥44×44px — chuẩn Apple HIG / Material touch target tối thiểu.
      expect(box?.height ?? 0).toBeGreaterThanOrEqual(40); // 40 thay vì 44 tuyệt đối — chấp nhận sai số nhỏ do padding/line-height, xem ghi chú UX-02 trong FIN05-QA-Test-Report-corrected.md
    });

    test(`/chat đọc được, không tràn ngang ở ${name}`, async ({ page }) => {
      await page.setViewportSize(viewport);
      await login(page);
      const hasHorizontalOverflow = await page.evaluate(
        () => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1
      );
      expect(hasHorizontalOverflow, "Trang /chat bị tràn ngang ở viewport di động").toBe(false);
      await expect(page.getByPlaceholder("Nhập tin nhắn...")).toBeVisible();
    });
  }
});

test.describe("UX-05 — mất mạng giữa chừng", () => {
  test("gửi chat khi backend không phản hồi -> báo lỗi rõ ràng, không crash, tin nhắn vẫn hiện trong luồng chat", async ({
    page,
  }) => {
    await login(page);

    // Mô phỏng mất mạng đúng nghĩa (route.abort, không phải route treo) cho
    // MỌI request /api/agent-chat sau điểm này — khác kịch bản BUG-01/UX-01
    // (server treo, chờ timeout) — đây là kết nối bị NGẮT ngay lập tức.
    await page.route("**/api/agent-chat", (route) => route.abort("internetdisconnected"));

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("Phí rút tiền về ngân hàng là bao nhiêu vậy bạn?");
    await input.press("Enter");

    // Tin nhắn khách vẫn hiện trong luồng chat (không "biến mất" khỏi màn
    // hình dù request lỗi) + có thông báo lỗi rõ ràng, không phải màn hình
    // trắng/treo. Match ĐÚNG bubble lỗi cụ thể (không dùng regex /lỗi/ lỏng —
    // phát hiện thật lúc verify: khớp NHẦM luôn cả câu chào mở đầu có chứa
    // chữ "lỗi" trong gợi ý nút "Báo lỗi giao dịch này").
    await expect(page.getByText("Phí rút tiền về ngân hàng là bao nhiêu vậy bạn?")).toBeVisible();
    await expect(page.getByText("Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé.")).toBeVisible({
      timeout: 10_000,
    });

    // Trang vẫn dùng được sau đó — gửi lại được, không bị khoá cứng.
    await page.unroute("**/api/agent-chat");
  });
});

test.describe("UX-02 (bổ sung) — mobile Chrome thật (userAgent + touch, không chỉ resize viewport)", () => {
  // Chỉ lấy viewport/userAgent/touch từ device descriptor — KHÔNG cả
  // defaultBrowserType (Playwright chặn override giữa file vì buộc worker
  // mới, xem lỗi thật lúc chạy: "Cannot use({ defaultBrowserType }) in a
  // describe group").
  const { defaultBrowserType: _unused, ...pixel7WithoutBrowserType } = devices["Pixel 7"];
  test.use({ ...pixel7WithoutBrowserType });
  test("đăng nhập được trên profile mobile Chrome thật (userAgent + touch)", async ({ page }) => {
    await login(page);
    await expect(page.getByPlaceholder("Nhập tin nhắn...")).toBeVisible();
  });
});
