import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * Cổng canh nhánh 403-role siết chặt (Coder, `b22782c`) — BA TRẠNG THÁI,
 * không được ngầm gộp (điều khoản Bảo Mật, QUYẾT ĐỊNH B): "không nhận ra ⟹
 * coi như X" là giấu mất một lỗi thật.
 *
 * 🔴 [ĐO 20/08] ① và ④ (chuỗi) XANH thật. ②③ ĐỎ lúc chạy đầu — Coder tự tay
 * xác nhận (grep thẳng ảnh đang chạy) đây là ẢNH FRONTEND CŨ HƠN CẢ hai
 * commit liên quan (`db0b064`/`b22782c`), KHÔNG PHẢI mock sai hay bug thật.
 * ② khớp đúng: ảnh cũ không biết `loai`, so message với bản CŨ (câu đầy đủ
 * khác câu rút gọn tôi mock) → không khớp → rơi vào nhánh chung, đúng y hệt
 * DOM quan sát được. ③ CHƯA giải thích trọn vẹn ngay cả khi đọc code cũ —
 * Coder chủ động dừng, không đoán tiếp trên ảnh sai, vì bất kể lý do gì thì
 * kết luận không đổi: ảnh này không phải thứ đang được kiểm.
 * CHƯA CHẠY LẠI — chờ DevOps dựng ảnh mới rồi chạy lại NGUYÊN FILE. Nếu ③
 * vẫn im lặng SAU KHI ảnh đúng, đó mới là finding thật cần theo tiếp.
 *
 *   ① 403 + message chứa "Cần role thuộc"  ⟹ banner LỆCH VAI (BannerLechVai)
 *   ② KHÔNG phải lỗi HTTP — response 200 OK, tool_calls[].result có
 *     loai="otp_het_tuoi" ⟹ mời xác thực OTP lại (tin nhắn bot, không phải banner)
 *   ③ 403 nhưng KHÔNG khớp "Cần role thuộc" ⟹ KHÔNG RÕ — hiện lỗi chung
 *     ("Có lỗi: ..."), TUYỆT ĐỐI không được hiện banner lệch vai
 *
 * Seam theo Coder khai trực tiếp (KHÔNG đọc frontend/src/, kể cả *.test.tsx
 * — phán quyết PO-agent 20/08: mọi thứ dưới src/ đều cấm đọc với tester, kể
 * cả file test cũ, vì nó mang theo điểm mù của người viết trước): chặn
 * `POST /api/agent-chat` bằng `page.route()`, trả JSON tự chọn.
 *
 * 🔴 Ca ③ là ca DUY NHẤT phân biệt được "siết" (b22782c) với "nới" (bản cũ,
 * regex lỏng `/role/i` khớp BẤT KỲ message nào chứa chữ "role"). Message
 * chọn CÓ CHỦ ĐÍCH: "Lỗi xác thực role nội bộ, vui lòng thử lại" — chứa
 * chữ "role" (để `/role/i.test(...)` === true, chứng minh ĐƯỢC bằng phép
 * thử chuỗi thuần, không cần dựng lại ảnh cũ) nhưng KHÔNG khớp chuỗi chặt
 * "Cần role thuộc" mà bản mới đòi. Nếu ai nới lại thành `/role/i` hoặc bỏ
 * vế chuỗi, ca ③ sẽ ĐỎ (banner lệch vai xuất hiện sai); ① và ② vẫn xanh —
 * đúng tính chất "chỉ ca này phân biệt được".
 *
 * 🔴 KHÔNG dựng cặp nhân quả bằng ảnh CŨ thật (checkout b22782c~1 + rebuild
 * frontend) — chi phí (dựng ảnh, Luật W, chiếm ngăn xếp dùng chung) không
 * tương xứng giá trị cho một ca hồi quy đã có bằng chứng chuỗi rõ ràng.
 * Khai theo đúng gợi ý PO-agon: "chưa có cặp nhân quả bằng ảnh thật", thay
 * bằng bằng chứng CHUỖI (xem test cuối file, 0 token, không cần trình duyệt).
 */
const CUSTOMER_PHONE = "0974000145";

const TEXT_LECH_VAI = "Bạn đang đăng nhập bằng tài khoản";
const TEXT_MOI_OTP = "Để tiếp tục thao tác này, mình cần bạn xác thực lại OTP phiên làm việc nhé.";
const MESSAGE_KHONG_RO = "Lỗi xác thực role nội bộ, vui lòng thử lại";

test.describe("Nhánh 403-role siết chặt (b22782c) — ba trạng thái, không gộp", () => {
  test("① 403 + 'Cần role thuộc' → banner LỆCH VAI", async ({ page }) => {
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    await page.route("**/api/agent-chat", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Cần role thuộc ['customer'], tài khoản hiện tại là cskh" }),
      })
    );

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("test lệch vai");
    await input.press("Enter");

    const banner = page.getByRole("alert").filter({ hasText: TEXT_LECH_VAI });
    await expect(banner, "Vế ① FAIL — không thấy banner lệch vai dù 403 khớp đúng 'Cần role thuộc'").toBeVisible({
      timeout: 15_000,
    });
  });

  test("② OTP hết tươi (200 OK, KHÔNG phải lỗi HTTP) → mời xác thực lại, KHÔNG phải lệch vai", async ({ page }) => {
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    await page.route("**/api/agent-chat", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          reply: "Mình cần xác thực lại trước khi tra tiếp.",
          tool_calls: [
            {
              tool_name: "lookup_transaction",
              args: {},
              result: {
                status: "error",
                loai: "otp_het_tuoi",
                message: "Lần xác thực OTP gần nhất đã quá hạn cho thao tác này.",
              },
            },
          ],
          ticket_id: null,
          should_escalate: null,
        }),
      })
    );

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("test otp het tuoi");
    await input.press("Enter");

    await expect(
      page.getByText(TEXT_MOI_OTP),
      "Vế ② FAIL — không thấy tin nhắn mời xác thực lại OTP dù tool result có loai=otp_het_tuoi"
    ).toBeVisible({ timeout: 15_000 });

    const banner = page.getByRole("alert").filter({ hasText: TEXT_LECH_VAI });
    await expect(banner, "Vế ② FAIL — OTP-hết-tươi KHÔNG được hiện banner lệch vai").toHaveCount(0);
  });

  test("③ 403 KHÔNG khớp 'Cần role thuộc' → KHÔNG RÕ, TUYỆT ĐỐI không hiện banner lệch vai", async ({ page }) => {
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    await page.route("**/api/agent-chat", (route) =>
      route.fulfill({
        status: 403,
        contentType: "application/json",
        body: JSON.stringify({ detail: MESSAGE_KHONG_RO }),
      })
    );

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("test khong ro");
    await input.press("Enter");

    await expect(
      page.getByText(`Có lỗi: ${MESSAGE_KHONG_RO}`),
      "Vế ③ FAIL — không thấy thông báo lỗi chung 'Có lỗi: ...' cho nhánh KHÔNG RÕ"
    ).toBeVisible({ timeout: 15_000 });

    const banner = page.getByRole("alert").filter({ hasText: TEXT_LECH_VAI });
    await expect(
      banner,
      "🔴 Vế ③ FAIL NGHIÊM TRỌNG — 403 KHÔNG khớp 'Cần role thuộc' nhưng VẪN hiện banner lệch vai. " +
        "Đây đúng lỗi 'không nhận ra ⟹ coi như X' mà điều khoản Bảo Mật cấm (QUYẾT ĐỊNH B) — " +
        "nhánh KHÔNG RÕ đang bị gộp ngầm vào lệch vai."
    ).toHaveCount(0);
  });
});

test.describe("Bằng chứng chuỗi thay cặp nhân quả ảnh cũ (0 token, không cần trình duyệt)", () => {
  test("MESSAGE_KHONG_RO CÓ khớp regex cũ /role/i — chứng minh ca ③ thật sự phân biệt được siết/nới", () => {
    // Không dựng lại ảnh b22782c~1 (đắt — cần rebuild frontend + Luật W).
    // Thay bằng bằng chứng chuỗi thuần: nếu bản CŨ (/role/i) còn chạy, nó
    // SẼ khớp message này (case-insensitive, chỉ cần chứa "role" ở đâu đó)
    // và sai lầm hiện banner lệch vai — đúng thứ ca ③ ở trên phải bắt được
    // nếu ai nới lại. Đây là chứng minh TOÁN HỌC về sức mạnh phân biệt của
    // ca ③, không phải chạy lại code cũ thật.
    expect(/role/i.test(MESSAGE_KHONG_RO)).toBe(true);
    // Và để chắc chắn ca ③ không vô tình khớp CẢ điều kiện MỚI (nếu khớp cả
    // hai thì ca ③ không đo được gì — phải chỉ khớp regex CŨ, không khớp
    // chuỗi chặt MỚI):
    expect(MESSAGE_KHONG_RO.includes("Cần role thuộc")).toBe(false);
  });
});
