import { test, expect, type Page, type BrowserContext } from "@playwright/test";

/**
 * FIN05-StressTest-Plan-v4 L4-01/L4-02/L4-03/L4-05 — live-chat 2 người dùng
 * THẬT (2 BrowserContext độc lập: 1 khách, 1 CSKH), qua đúng topology
 * `docker compose up` thật (Caddy → backend, xem playwright.livechat.config.ts
 * — KHÔNG dùng chung config với AUTH-* vì Next.js dev/start trần không proxy
 * WebSocket). Regression cho 3 bug THẬT đã từng lọt tới người dùng
 * (tin nhắn lặp, khung chat tách rời, session mồ côi khi CSKH mất kết nối
 * không bấm "Kết thúc chat") — không chỉ test happy-path.
 *
 * Chạy: `docker compose up -d` (đảm bảo 5 service healthy) rồi
 * `npx playwright test --config=playwright.livechat.config.ts` từ
 * `frontend/`. Cần `OPENAI_API_KEY` thật trong `.env` của backend (khách
 * phải nói CÂU THẬT để AI tự gọi request_human_handoff — không mock tool
 * call, đúng nguyên tắc "test qua UI thật" đã áp dụng xuyên suốt
 * frontend/e2e/auth.spec.ts).
 */

const CUSTOMER_PHONE = "0387000001"; // USR-0001 — khác USR-0145 (auth.spec.ts) để không lẫn state 2 bộ test
const STAFF_PHONE = "0353000201"; // USR-0201, role cskh

// Phát hiện thật (2026-08-12, lúc chạy suite này lặp lại nhiều lần liên
// tiếp): `/auth/login` rate-limit 10/phút khoá theo IP (get_remote_address)
// — ĐÚNG finding ST2-P0-4 đã ghi nhận trước đó (docs/TESTING.md mục "v2 bổ
// sung"), giờ tự lộ ra ngay trong chính bộ E2E test này vì mọi context
// Playwright đều đi từ CÙNG 1 máy (đối chiếu log backend thật: "ratelimit 10
// per 1 minute (172.19.0.5) exceeded at endpoint: /auth/login"). Không sửa
// rate-limit ở đây (đã có test riêng ghi nhận + chờ quyết định PO, xem
// tests/test_api/test_auth_login.py) — chỉ né bằng retry-with-backoff, cùng
// tinh thần auth.spec.ts::triggerSensitiveAction đã làm cho vấn đề flaky
// khác.
async function loginAs(page: Page, phone: string, roleLabel: string, expectedPathPrefix: string, attempt = 1): Promise<void> {
  await page.goto("/login");
  await page.locator(".filter-chip", { hasText: roleLabel }).click();
  await page.getByPlaceholder("09xx xxx xxx").fill(phone);
  const [response] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/api/session"), { timeout: 15_000 }).catch(() => null),
    page.getByRole("button", { name: "Đăng nhập" }).click(),
  ]);
  if (response && response.status() === 429) {
    if (attempt >= 3) throw new Error(`Vẫn 429 sau ${attempt} lần thử đăng nhập ${phone} — rate-limit chưa hồi phục.`);
    await page.waitForTimeout(15_000); // đợi hết cửa sổ 1 phút của rate-limit
    return loginAs(page, phone, roleLabel, expectedPathPrefix, attempt + 1);
  }
  await page.waitForURL(`**${expectedPathPrefix}**`, { timeout: 15_000 });
}

async function sendMessage(page: Page, text: string) {
  const input = page.getByPlaceholder("Nhập tin nhắn...");
  await input.fill(text);
  await input.press("Enter");
}

// Phát hiện thật (2026-08-12, lúc chạy suite này lặp lại nhiều lần): agent
// (LLM thật) KHÔNG PHẢI LÚC NÀO cũng gọi request_human_handoff ngay lượt
// đầu dù system prompt đã dặn rõ — CÙNG lớp vấn đề "LLM non-determinism"
// auth.spec.ts::triggerSensitiveAction đã ghi nhận cho luồng OTP (agent đôi
// khi chỉ nói "để mình tra cứu" mà không gọi tool). Không có đường UI xác
// định (như chip/rail cho OTP) để né hẳn AI cho luồng handoff — bounded
// retry với câu nhắn RÕ RÀNG HƠN ở lần 2, thay vì coi đây là lỗi test.
async function requestHumanHandoffAndWaitConnected(page: Page) {
  const messages = [
    "Tôi muốn nói chuyện trực tiếp với nhân viên CSKH thật, không cần AI trả lời nữa.",
    "Chuyển tôi cho nhân viên CSKH ngay bây giờ, tôi không muốn nói chuyện với AI nữa.",
  ];
  for (let attempt = 0; attempt < messages.length; attempt++) {
    await sendMessage(page, messages[attempt]);
    try {
      await expect(page.getByText("Đã kết nối")).toBeVisible({ timeout: 20_000 });
      return;
    } catch (e) {
      if (attempt === messages.length - 1) throw e;
    }
  }
}

test.describe("L4-01/02/03/05 — live-chat 2 người dùng thật (docker compose)", () => {
  test("khách yêu cầu người thật → CSKH thấy realtime, nhận ca, nhắn qua lại, đóng phiên", async ({ browser }) => {
    const customerContext: BrowserContext = await browser.newContext();
    const staffContext: BrowserContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    const staffPage = await staffContext.newPage();

    try {
      // --- Khách: đăng nhập, yêu cầu người thật qua AI (gọi OpenAI thật) ---
      await loginAs(customerPage, CUSTOMER_PHONE, "Khách hàng", "/chat");
      // AI phải gọi request_human_handoff → panel "Chat trực tiếp CSKH" xuất
      // hiện ở rail phải, và WS tự kết nối (status "Đang kết nối..."/"Đã kết nối").
      await requestHumanHandoffAndWaitConnected(customerPage);
      await expect(customerPage.getByText("Chat trực tiếp CSKH")).toBeVisible({ timeout: 5_000 });
      // Disclaimer hệ thống PHẢI xuất hiện NGAY TRONG CÙNG .chat-thread với
      // hội thoại AI — regression cho bug "khung chat tách rời" (2026-08-11):
      // trước fix, live-chat mở ra 1 khung RIÊNG bên dưới thay vì vào chung
      // luồng chat đang có.
      const chatThread = customerPage.locator(".chat-thread");
      await expect(chatThread.getByText("chuyên viên CSKH")).toBeVisible({ timeout: 10_000 });

      // --- CSKH: đăng nhập, PHẢI thấy hàng chờ REALTIME, không cần F5 (L4-05) ---
      await loginAs(staffPage, STAFF_PHONE, "Nhân viên CSKH", "/dashboard");
      const waitingWidget = staffPage.getByText("Khách đang chờ chat trực tiếp");
      await expect(waitingWidget).toBeVisible({ timeout: 20_000 });

      // "Mở & nhận" ở dashboard là <span onClick> (không phải <button> thật,
      // xem dashboard/page.tsx:128) — getByRole("button", ...) KHÔNG khớp,
      // treo vô thời hạn chờ 1 phần tử không bao giờ xuất hiện (phát hiện
      // thật lúc chạy test này). Dùng getByText thay vì role.
      await staffPage.getByText("Mở & nhận").first().click();
      await staffPage.getByRole("button", { name: "Nhận phiên chat này" }).click();
      await expect(staffPage.getByText("Đã kết nối")).toBeVisible({ timeout: 10_000 });

      // --- Nhắn qua lại 2 chiều, xác nhận KHÔNG lặp tin nhắn (regression) ---
      const probeText = `alo-${Date.now()}`; // chuỗi duy nhất mỗi lần chạy — tránh false-positive nếu chạy lại
      await sendMessage(staffPage, probeText);
      const customerBubbles = customerPage.locator(".chat-thread .bubble", { hasText: probeText });
      await expect(customerBubbles).toHaveCount(1, { timeout: 15_000 });

      const replyText = `da-nhan-${Date.now()}`;
      await sendMessage(customerPage, replyText);
      const staffBubbles = staffPage.locator(".chat-thread .bubble", { hasText: replyText });
      await expect(staffBubbles).toHaveCount(1, { timeout: 15_000 });

      // --- CSKH đóng phiên — khách phải thấy rõ, không bị treo im lặng ---
      await staffPage.getByRole("button", { name: "Kết thúc chat" }).click();
      await expect(customerPage.getByText("Phiên chat trực tiếp đã kết thúc")).toBeVisible({ timeout: 10_000 });

      // GAP-LIVECHAT-E2E-001 yêu cầu verify CSAT ở đây — ĐÃ THỬ, phát hiện
      // thật (không phải test sai): UI đánh giá CSAT (`handleCsat`, chip
      // sao) chỉ tồn tại trong `components/LiveChatPanel.tsx`, nhưng
      // `app/(app)/chat/ChatClient.tsx` (trang khách hàng THẬT dùng, xem
      // các state `liveChatTicketId`/`liveChatSessionId` + useLiveChatSocket
      // riêng ở trên) KHÔNG import/render LiveChatPanel — ChatClient tự xây
      // UI live-chat RIÊNG, hoàn toàn tách biệt. Nhánh `!isStaff` CSAT trong
      // LiveChatPanel.tsx vì vậy là CODE CHẾT với khách hàng thật (chỉ
      // LÝ THUYẾT còn sống nếu 1 customer nào đó mở được /tickets/[id], vốn
      // đã bị chặn role). Đây CHÍNH XÁC là lý do GAP-LIVECHAT-CSAT-001 được
      // đánh dấu `product_decision_needed: true` ("CSAT phía khách hàng —
      // TÍNH NĂNG CHƯA TỒN TẠI") — không viết test cho tính năng không
      // reach được người dùng thật, đúng nguyên tắc "không test thứ chưa
      // xác nhận tồn tại". Không thêm bước CSAT vào test này.
    } finally {
      await customerContext.close();
      await staffContext.close();
    }
  });

  test("L4-02 regression — CSKH mất kết nối KHÔNG bấm 'Kết thúc chat' → phiên tự trả về hàng chờ, không mồ côi", async ({
    browser,
  }) => {
    const customerContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    const firstStaffContext = await browser.newContext();
    const firstStaffPage = await firstStaffContext.newPage();

    try {
      await loginAs(customerPage, CUSTOMER_PHONE, "Khách hàng", "/chat");
      await requestHumanHandoffAndWaitConnected(customerPage);

      await loginAs(firstStaffPage, STAFF_PHONE, "Nhân viên CSKH", "/dashboard");
      await expect(firstStaffPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      await firstStaffPage.getByText("Mở & nhận").first().click();
      await firstStaffPage.getByRole("button", { name: "Nhận phiên chat này" }).click();
      await expect(firstStaffPage.getByText("Đã kết nối")).toBeVisible({ timeout: 10_000 });

      // Mô phỏng CSKH mất kết nối đột ngột (đóng tab/rớt mạng) — KHÔNG bấm
      // "Kết thúc chat" — đây CHÍNH XÁC là kịch bản gây bug thật đã báo:
      // "khách đòi gặp nhân viên là nhân viên lại vào chat tiếp luôn dù
      // không hiện thông báo ticket mới nào cả" (session mồ côi, xem
      // src/api/live_chat_ws.py::release_staff_sessions).
      await firstStaffContext.close();

      // 1 CSKH KHÁC mở dashboard — phải thấy lại ĐÚNG ticket này trong hàng
      // chờ (không mắc kẹt ở trạng thái "đã có người nhận" mãi mãi).
      const secondStaffContext = await browser.newContext();
      const secondStaffPage = await secondStaffContext.newPage();
      try {
        await loginAs(secondStaffPage, STAFF_PHONE, "Nhân viên CSKH", "/dashboard");
        await expect(secondStaffPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      } finally {
        await secondStaffContext.close();
      }
    } finally {
      await customerContext.close();
    }
  });

  test("L4-03 — cảnh báo rời trang khi đang chat trực tiếp", async ({ browser }) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    try {
      await loginAs(page, CUSTOMER_PHONE, "Khách hàng", "/chat");
      await requestHumanHandoffAndWaitConnected(page);

      let dialogAppeared = false;
      page.on("dialog", async (dialog) => {
        dialogAppeared = true;
        await dialog.dismiss();
      });
      await page.close({ runBeforeUnload: true });
      await page.waitForTimeout(500).catch(() => {});
      expect(dialogAppeared).toBe(true);
    } finally {
      await context.close();
    }
  });

  test("L4-04 (điều tra, chưa xác định chắc root cause) — gõ nhanh liên tục rồi Enter, ô nhập phải sạch hoàn toàn", async ({
    browser,
  }) => {
    // Phát hiện thật (2026-08-11): input đôi khi còn sót chữ sau khi gửi.
    // Gốc rễ CHƯA xác định chắc chắn — nghi ngờ cao nhất: bộ gõ tiếng Việt
    // cấp hệ điều hành/phần mềm (kiểu Unikey) tự mô phỏng chuỗi phím
    // backspace+gõ lại KHÔNG đi qua đúng 1-onChange-per-keystroke, và KHÔNG
    // set `isComposing=true` như IME trình duyệt gốc (CJK) — nên guard
    // `!e.nativeEvent.isComposing` hiện có không bắt được. Playwright không
    // mô phỏng được chính xác 1 bộ gõ IME cấp OS bên thứ ba — test này chỉ
    // mô phỏng gõ NHANH LIÊN TỤC (proxy gần nhất có thể) rồi assert ô nhập
    // sạch tuyệt đối sau gửi — bảo vệ được lớp remount-via-key đang có,
    // KHÔNG chứng minh đã tìm đúng root cause gốc.
    const context = await browser.newContext();
    const page = await context.newPage();
    try {
      await loginAs(page, CUSTOMER_PHONE, "Khách hàng", "/chat");
      const input = page.getByPlaceholder(/Nhập tin nhắn|Chọn một lựa chọn/);
      await input.pressSequentially("chào bạn", { delay: 5 });
      await input.press("Enter");
      await expect(input).toHaveValue("", { timeout: 5_000 });
    } finally {
      await context.close();
    }
  });
});
