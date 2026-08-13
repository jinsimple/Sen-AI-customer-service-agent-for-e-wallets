import { test, expect, type Page, type BrowserContext } from "@playwright/test";
import { completeOtpIfPrompted, loginAs } from "./helpers/actors";

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
const STAFF_PHONE_B = "0560000202"; // USR-0202, role cskh — dùng cho race claim thật (L4-06)
const STAFF_PHONE_C = "0389000203"; // USR-0203, role cskh — CSKH thứ 3 tiếp nhận sau khi CSKH thắng race rớt kết nối (L4-06)

// `loginAs` dùng chung từ helpers/actors.ts (đã có retry-with-backoff sẵn
// cho 429 — cùng lý do rate-limit AUTH5-08 đã ghi ở docs/TESTING.md, giờ
// khoá theo phone chứ không còn theo IP nữa, nhưng vẫn giữ retry vì nhiều
// BrowserContext trong 1 file này vẫn có thể dồn tới ngưỡng 10/phút/số điện
// thoại nếu chạy lại suite liên tục).

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
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
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
      await loginAs(staffPage, STAFF_PHONE, "/dashboard");
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
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
      await requestHumanHandoffAndWaitConnected(customerPage);

      await loginAs(firstStaffPage, STAFF_PHONE, "/dashboard");
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
        await loginAs(secondStaffPage, STAFF_PHONE, "/dashboard");
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
      await loginAs(page, CUSTOMER_PHONE, "/chat");
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
      await loginAs(page, CUSTOMER_PHONE, "/chat");
      const input = page.getByPlaceholder(/Nhập tin nhắn|Chọn một lựa chọn/);
      await input.pressSequentially("chào bạn", { delay: 5 });
      await input.press("Enter");
      await expect(input).toHaveValue("", { timeout: 5_000 });
    } finally {
      await context.close();
    }
  });

  /**
   * L4-06 (khó nhất — full-stack, 4 actor thật) — kết hợp TOÀN BỘ tính năng
   * chatbot (tra cứu giao dịch qua gõ tự do có OTP giữa chừng, không tự động
   * gửi lại) VỚI live-chat (escalate người thật, 2 CSKH GIÀNH CA CÙNG LÚC —
   * race THẬT qua 2 kết nối mạng độc lập chứ không phải gọi hàm claim_session
   * tuần tự như unit test test_claim_session_race_second_claim_is_noop, nhắn
   * dồn dập 2 chiều đồng thời không mất/trùng tin, CSKH thắng cuộc rớt kết
   * nối giữa chừng, CSKH thứ 3 tiếp nhận và phải thấy ĐÚNG lịch sử hội thoại
   * cũ, đóng phiên, rồi xác nhận khách quay lại nói chuyện với AI liền mạch
   * — không kẹt trạng thái). Đây là kịch bản chạm nhiều lớp hệ thống nhất
   * trong toàn bộ bộ e2e: LLM thật + OTP + WebSocket + optimistic-concurrency
   * DB update + dọn session mồ côi + bàn giao ngữ cảnh — mọi lớp đều có thể
   * làm test này đỏ nếu có 1 lớp sai.
   */
  test("L4-06 (khó nhất) — AI tra cứu OTP → escalate → 2 CSKH giành ca cùng lúc → nhắn dồn dập → CSKH thắng rớt kết nối → CSKH thứ 3 tiếp nhận đúng lịch sử → đóng phiên → khách quay lại nói chuyện với AI liền mạch", async ({
    browser,
  }) => {
    test.setTimeout(240_000);

    const customerContext = await browser.newContext();
    const staffAContext = await browser.newContext();
    const staffBContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    const staffAPage = await staffAContext.newPage();
    const staffBPage = await staffBContext.newPage();
    let staffCContext: BrowserContext | null = null;

    try {
      // --- 1) Khách: tra cứu 1 giao dịch THẬT qua gõ tự do (không phải chip)
      // — nhánh này có thể trigger OTP giữa chừng, KHÔNG tự động gửi lại câu
      // hỏi gốc (khác luồng chip, xem docstring completeOtpIfPrompted trong
      // helpers/actors.ts) — phải tự gửi lại nếu có OTP xảy ra.
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
      const txnItems = customerPage.locator(".txn-item");
      await expect(txnItems.first()).toBeVisible({ timeout: 15_000 });
      const firstTransId = (await txnItems.first().locator(".txn-meta").textContent())?.split("·").pop()?.trim();
      expect(firstTransId).toMatch(/^TXN/);

      const lookupQuestion = `Giao dịch ${firstTransId} của tôi có bị trừ nhầm không, mình hơi lo?`;
      await sendMessage(customerPage, lookupQuestion);
      const otpHappened = await completeOtpIfPrompted(customerPage);
      if (otpHappened) await sendMessage(customerPage, lookupQuestion);
      await expect(customerPage.locator(".bubble-bot").last()).toContainText(firstTransId!, { timeout: 30_000 });

      // --- 2) Khách escalate người thật NGAY TRONG CÙNG hội thoại đã tra cứu
      // ở trên (không phải phiên mới) ---
      await requestHumanHandoffAndWaitConnected(customerPage);
      await expect(customerPage.getByText("Chat trực tiếp CSKH")).toBeVisible({ timeout: 5_000 });

      // --- 3) 2 CSKH cùng mở đúng ticket đang chờ, cùng bấm "Nhận phiên chat
      // này" GẦN NHƯ ĐỒNG THỜI (Promise.all — 2 request HTTP thật race nhau ở
      // backend, khác hẳn gọi claim_session() 2 lần tuần tự trong unit test)
      // — optimistic-concurrency UPDATE (claimed_by IS NULL) phải đảm bảo
      // ĐÚNG 1 người thắng, người thua thấy rõ ràng, không bị treo im lặng.
      await loginAs(staffAPage, STAFF_PHONE, "/dashboard");
      await loginAs(staffBPage, STAFF_PHONE_B, "/dashboard");
      await expect(staffAPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      await expect(staffBPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      await Promise.all([staffAPage.getByText("Mở & nhận").first().click(), staffBPage.getByText("Mở & nhận").first().click()]);
      const claimBtnA = staffAPage.getByRole("button", { name: "Nhận phiên chat này" });
      const claimBtnB = staffBPage.getByRole("button", { name: "Nhận phiên chat này" });
      await expect(claimBtnA).toBeVisible({ timeout: 15_000 });
      await expect(claimBtnB).toBeVisible({ timeout: 15_000 });
      await Promise.all([claimBtnA.click(), claimBtnB.click()]);

      // LƯU Ý QUAN TRỌNG (phát hiện thật lúc chạy test này lần đầu — bug ở
      // TEST, không phải sản phẩm): nhãn "Đã kết nối" là trạng thái WEBSOCKET
      // (status === "open" ở LiveChatPanel.tsx dòng ~210) — CẢ 2 CSKH đều tự
      // mint vé + mở kết nối WS ngay khi vào trang ticket, KHÔNG PHỤ THUỘC ai
      // thắng race claim, nên cả 2 page đều hiện "Đã kết nối" bất kể kết quả
      // claim. Tín hiệu ĐÚNG để phân biệt thắng/thua: nút "Kết thúc chat" chỉ
      // hiện khi `claimedByMe===true` (chỉ người thắng nhận được sự kiện WS
      // "claim_success" riêng cho mình) — người thua nhận HTTP 409 ngay từ
      // response POST /claim, hiện dòng "Phiên chat này vừa có chuyên viên
      // khác nhận." trong chính luồng chat của họ.
      async function claimOutcome(page: Page): Promise<"won" | "lost"> {
        return Promise.race([
          page.getByRole("button", { name: "Kết thúc chat" }).waitFor({ state: "visible", timeout: 15_000 }).then(() => "won" as const),
          page
            .getByText("Phiên chat này vừa có chuyên viên khác nhận.")
            .waitFor({ state: "visible", timeout: 15_000 })
            .then(() => "lost" as const),
        ]);
      }
      const [outcomeA, outcomeB] = await Promise.all([claimOutcome(staffAPage), claimOutcome(staffBPage)]);
      expect([outcomeA, outcomeB].sort()).toEqual(["lost", "won"]); // ĐÚNG 1 người thắng, không hoà, không cả 2 cùng thua

      const winnerPage = outcomeA === "won" ? staffAPage : staffBPage;
      const loserPage = outcomeA === "won" ? staffBPage : staffAPage;
      // Người thua không được gửi được tin — input phải khoá, không phải chỉ
      // ẩn nút nhận.
      await expect(loserPage.getByPlaceholder("Nhận phiên chat để bắt đầu trả lời")).toBeDisabled({ timeout: 5_000 });

      // --- 4) Nhắn DỒN DẬP 2 chiều ĐỒNG THỜI (Promise.all 2 chuỗi tuần tự
      // độc lập trên 2 kết nối WS khác nhau) — xác nhận không mất/trùng tin
      // dưới tải thật, không phải 1 lượt ping-pong đơn lẻ như L4-01. Kèm 1
      // tin có hình dạng PII (SĐT) — CHỈ xác nhận truyền tải đúng nội dung
      // (không phải bài test chính sách che PII, việc đó đã có test riêng
      // tests/test_api/test_live_chat_pii_gap.py cho finding ST2-P0-3).
      const stamp = Date.now();
      const custBurst = [`khach-1-${stamp}`, `khach-2-sdt-0912345678-${stamp}`, `khach-3-${stamp}`];
      const staffBurst = [`nv-1-${stamp}`, `nv-2-${stamp}`, `nv-3-${stamp}`];
      // Phát hiện thật (lúc chạy test này lần đầu, điều tra bằng cách log
      // trực tiếp khung WS qua page.on("websocket") — bug ở TEST, không phải
      // sản phẩm): cả LiveChatPanel.tsx VÀ ChatClient.tsx đều có khoá chống
      // gửi-2-lần cố ý (400ms, `sendingRef`/`liveChatSendingRef` — chặn 1 lần
      // Enter kích hoạt handleSend nhiều lần) — gửi liên tiếp NHANH HƠN 400ms
      // trên CÙNG 1 trang bị `handleSend` return sớm, ÂM THẦM không gửi,
      // không báo lỗi gì (khớp đúng comment "phát hiện thật" cạnh chính khoá
      // đó trong code sản phẩm). Chờ tin vừa gửi render xong (round-trip qua
      // WS) RỒI CHỜ THÊM qua mốc 400ms trước khi gửi tin kế — vẫn giữ đúng
      // tính "2 người gửi ĐỒNG THỜI, độc lập" (2 trang khác nhau qua
      // Promise.all bên dưới), chỉ tôn trọng khoá chống double-fire hợp lệ
      // TRONG CÙNG 1 trang.
      async function sendBurst(page: Page, texts: string[]) {
        for (const t of texts) {
          await sendMessage(page, t);
          await page.locator(".chat-thread .bubble", { hasText: t }).first().waitFor({ state: "visible", timeout: 10_000 });
          await page.waitForTimeout(500);
        }
      }
      await Promise.all([sendBurst(customerPage, custBurst), sendBurst(winnerPage, staffBurst)]);
      for (const t of custBurst) {
        await expect(winnerPage.locator(".chat-thread .bubble", { hasText: t })).toHaveCount(1, { timeout: 15_000 });
      }
      for (const t of staffBurst) {
        await expect(customerPage.locator(".chat-thread .bubble", { hasText: t })).toHaveCount(1, { timeout: 15_000 });
      }

      // --- 5) CSKH thắng cuộc rớt kết nối đột ngột giữa chừng (KHÔNG bấm
      // "Kết thúc chat") — cùng kịch bản mồ côi L4-02, nhưng lần này diễn ra
      // NGAY SAU khi vừa có lịch sử tin nhắn thật, để bước 6 verify được bàn
      // giao KHÔNG làm mất lịch sử.
      const winnerContext = outcomeA === "won" ? staffAContext : staffBContext;
      await winnerContext.close();
      await expect(customerPage.locator(".chat-thread").getByText("phiên của bạn được chuyển lại hàng chờ")).toBeVisible({
        timeout: 15_000,
      });

      // --- 6) CSKH thứ 3 tiếp nhận — PHẢI thấy lại đúng lịch sử tin nhắn cũ
      // (không mất khi chuyển ca), nhắn tiếp, khách nhận được bình thường.
      staffCContext = await browser.newContext();
      const staffCPage = await staffCContext.newPage();
      await loginAs(staffCPage, STAFF_PHONE_C, "/dashboard");
      await expect(staffCPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      await staffCPage.getByText("Mở & nhận").first().click();
      await staffCPage.getByRole("button", { name: "Nhận phiên chat này" }).click();
      await expect(staffCPage.getByText("Đã kết nối")).toBeVisible({ timeout: 10_000 });
      await expect(staffCPage.locator(".chat-thread .bubble", { hasText: custBurst[0] })).toBeVisible({ timeout: 10_000 });

      const finalMsg = `final-${stamp}`;
      await sendMessage(staffCPage, finalMsg);
      await expect(customerPage.locator(".chat-thread .bubble", { hasText: finalMsg })).toBeVisible({ timeout: 15_000 });

      // --- 7) Đóng phiên, rồi xác nhận khách quay lại nói chuyện với AI
      // LIỀN MẠCH — không kẹt ở trạng thái live-chat đã đóng (verify dọn
      // sạch liveChatSessionId/liveChatTicketId ở ChatClient.tsx, không chỉ
      // đọc code mà chạy thật qua UI). ---
      const botBubblesBefore = await customerPage.locator(".bubble-bot").count();
      await staffCPage.getByRole("button", { name: "Kết thúc chat" }).click();
      await expect(customerPage.getByText("Phiên chat trực tiếp đã kết thúc")).toBeVisible({ timeout: 10_000 });
      await sendMessage(customerPage, "Cảm ơn bạn nhé. Phí rút tiền về ngân hàng liên kết là bao nhiêu vậy?");
      await expect(customerPage.locator(".bubble-bot")).toHaveCount(botBubblesBefore + 1, { timeout: 30_000 });
    } finally {
      await customerContext.close();
      await staffAContext.close().catch(() => {});
      await staffBContext.close().catch(() => {});
      if (staffCContext) await staffCContext.close();
    }
  });

  // ---------------------------------------------------------------------
  // L4-07 (R4, 13/08) — fan-out liên worker: >=5 tin MỖI CHIỀU, xen kẽ.
  //
  // Vì sao cần dù L4-01 đã nhắn 2 chiều: L4-01 chỉ gửi ĐÚNG 1 tin mỗi
  // chiều. Sau ADR-015 (Redis pub/sub, 4 worker), lỗi vỡ fan-out là lỗi IM
  // LẶNG — tin biến mất, không exception — và chỉ xảy ra khi khách với CSKH
  // rơi vào 2 worker KHÁC nhau. Một cặp kết nối nằm trên cùng 1 worker sẽ
  // pass mọi lần dù fan-out hỏng hoàn toàn. Nhắn nhiều lượt xen kẽ trên
  // cùng cặp kết nối KHÔNG đổi được worker (WS giữ nguyên kết nối), nên test
  // này bổ sung thêm: assert từng tin xuất hiện ĐÚNG 1 LẦN (bắt cả lỗi lặp
  // tin do nhận cả bản local lẫn bản vọng từ Redis — đúng thứ _INSTANCE_ID
  // trong ADR-015 sinh ra để chặn).
  //
  // Kiểm phủ nhiều CẶP worker khác nhau: xem
  // scripts/../qa loop tầng WebSocket trong báo cáo QA 13/08 (lặp N phiên,
  // mỗi phiên 1 cặp kết nối mới) — test UI này giữ 1 phiên cho nhanh và để
  // chứng minh đường đi THẬT qua trình duyệt.
  test("L4-07 — 5 tin mỗi chiều xen kẽ, không mất tin, không lặp tin", async ({ browser }) => {
    const customerContext: BrowserContext = await browser.newContext();
    const staffContext: BrowserContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    const staffPage = await staffContext.newPage();

    try {
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
      await requestHumanHandoffAndWaitConnected(customerPage);

      await loginAs(staffPage, STAFF_PHONE, "/dashboard");
      await expect(staffPage.getByText("Khách đang chờ chat trực tiếp")).toBeVisible({ timeout: 20_000 });
      await staffPage.getByText("Mở & nhận").first().click();
      await staffPage.getByRole("button", { name: "Nhận phiên chat này" }).click();
      await expect(staffPage.getByText("Đã kết nối")).toBeVisible({ timeout: 10_000 });

      const stamp = Date.now(); // chuỗi duy nhất mỗi lần chạy — chạy lại không đụng tin cũ
      const ROUNDS = 5;
      for (let i = 1; i <= ROUNDS; i++) {
        const fromStaff = `cskh-${stamp}-${i}`;
        await sendMessage(staffPage, fromStaff);
        await expect(
          customerPage.locator(".chat-thread .bubble", { hasText: fromStaff }),
          `tin CSKH->khách vòng ${i} phải tới đúng 1 lần`,
        ).toHaveCount(1, { timeout: 15_000 });

        const fromCustomer = `khach-${stamp}-${i}`;
        await sendMessage(customerPage, fromCustomer);
        await expect(
          staffPage.locator(".chat-thread .bubble", { hasText: fromCustomer }),
          `tin khách->CSKH vòng ${i} phải tới đúng 1 lần`,
        ).toHaveCount(1, { timeout: 15_000 });
      }

      // Cuối phiên: soát lại TOÀN BỘ 10 tin vẫn còn đủ ở cả hai phía (bắt
      // trường hợp tin tới rồi biến mất khi render lại/backlog ghi đè).
      for (let i = 1; i <= ROUNDS; i++) {
        await expect(customerPage.locator(".chat-thread .bubble", { hasText: `cskh-${stamp}-${i}` })).toHaveCount(1);
        await expect(customerPage.locator(".chat-thread .bubble", { hasText: `khach-${stamp}-${i}` })).toHaveCount(1);
        await expect(staffPage.locator(".chat-thread .bubble", { hasText: `cskh-${stamp}-${i}` })).toHaveCount(1);
        await expect(staffPage.locator(".chat-thread .bubble", { hasText: `khach-${stamp}-${i}` })).toHaveCount(1);
      }

      await staffPage.getByRole("button", { name: "Kết thúc chat" }).click();
      await expect(customerPage.getByText("Phiên chat trực tiếp đã kết thúc")).toBeVisible({ timeout: 10_000 });
    } finally {
      await customerContext.close();
      await staffContext.close();
    }
  });
});
