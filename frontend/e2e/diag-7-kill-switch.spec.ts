import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

// TẠM THỜI, KHÔNG COMMIT — chẩn đoán ⑦ một lần, buổi tốn phí 25/08.
// Tiêu chí MỚI (Coder + Lead duyệt 25/08): tắt TRIAGE_ENABLED + T0_GATE_ENABLED
// (OTP_GATE_GROUP_B_ENABLED vẫn bật, cố ý) ⟹ KHÔNG được xuất hiện duong=nhe /
// thu_slot / otp_resend_thu_slot trong sổ. duong=can_otp VẪN là bình thường
// (④ đang sống, không thuộc hai cờ vừa tắt).

interface PhanHoi {
  duong?: string;
  usage?: { total_tokens?: number };
  [key: string]: unknown;
}
const PHONE = "0974000145";

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error("chưa đăng nhập?");
  return session;
}

function hook(page: import("@playwright/test").Page): PhanHoi[] {
  const responses: PhanHoi[] = [];
  page.on("response", async (res) => {
    if (res.url().includes("/api/agent-chat") && res.status() === 200) {
      try { responses.push(await res.json()); } catch { /* noop */ }
    }
  });
  return responses;
}

test("chẩn đoán ⑦ — không được có nhe/thu_slot/otp_resend_thu_slot trong sổ", async ({ page, context }) => {
  test.setTimeout(120_000);
  await loginAs(page, PHONE, "/chat");
  const real = await readSessionCookie(context);
  await setForgedSessionCookie(context, forgeOtpVerifiedAt(real, null));
  await page.reload();
  const responses = hook(page);
  const input = page.getByPlaceholder("Nhập tin nhắn...");

  // Probe 1 — câu xã giao thuần, BÌNH THƯỜNG kích "nhe" khi TRIAGE_ENABLED=1.
  await input.fill("alo");
  await input.press("Enter");
  await expect.poll(() => responses.length, { timeout: 20_000 }).toBeGreaterThan(0);
  console.log("PROBE 1 (alo, pre-OTP) duong =", responses[0].duong);

  // Probe 2 — khiếu nại cá nhân thiếu số tiền, pre-OTP: PHẢI vẫn can_otp (④ sống).
  await input.fill("tôi bị trừ tiền");
  await input.press("Enter");
  await expect.poll(() => responses.length, { timeout: 20_000 }).toBeGreaterThan(1);
  console.log("PROBE 2 (khiếu nại thiếu tiền, pre-OTP) duong =", responses[1].duong);

  const otpHappened = await completeOtpIfPrompted(page, 40_000);
  console.log("OTP xảy ra:", otpHappened);
  if (otpHappened) {
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
  }

  // Probe 3 — gửi lại CÙNG câu thiếu tiền sau OTP: bình thường sẽ là
  // otp_resend_thu_slot (T0) khi T0_GATE_ENABLED=1; PHẢI đổi thành day_du khi =0.
  const before = responses.length;
  await input.fill("tôi bị trừ tiền");
  await input.press("Enter");
  await expect.poll(() => responses.length, { timeout: 30_000 }).toBeGreaterThan(before);
  const p3 = responses[responses.length - 1];
  console.log("PROBE 3 (cùng câu, sau OTP) duong =", p3.duong, "usage =", JSON.stringify(p3.usage));

  const capMoTa: (string | undefined)[] = [responses[0]?.duong, responses[1]?.duong, p3.duong];
  console.log("TÓM TẮT SỔ 3 PROBE:", JSON.stringify(capMoTa));
  for (const d of capMoTa) {
    expect(["nhe", "thu_slot", "otp_resend_thu_slot"].includes(d ?? ""), `duong=${d} — ⑦ HỎNG THẬT`).toBe(false);
  }
});
