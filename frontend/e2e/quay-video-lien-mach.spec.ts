import { test, expect, type Page } from "@playwright/test";
import hoiThoai from "./quay-video.hoithoai.json";

// ---------------------------------------------------------------------------
// VIDEO TRÌNH SẢN PHẨM FIN-05 — MỘT TỆP LIỀN MẠCH, 6 cảnh, ~180 giây.
//
// 🔴 TỆP NÀY DO **PO** VIẾT. `frontend/` là vùng ghi `tech-lead` theo
//    CLAUDE.md §4; PO thật cấp quyền mở rộng TẠM THỜI 28/08 cho đúng việc quay.
//    Khai ra để KHÔNG thành tiền lệ im lặng.
//
// VÌ SAO MỘT TEST CHỨ KHÔNG SÁU: Playwright ghi MỘT video mỗi test. Sáu test
// cho sáu tệp rời, mà ffmpeg đi kèm Playwright bị cắt còn 24 filter — KHÔNG có
// concat, KHÔNG có subtitles. Gộp thành một test ⟹ một tệp liền mạch, và phụ
// đề khắc bằng chính trình duyệt. Không phụ thuộc công cụ ngoài nào.
//
// BA LUẬT CỨNG:
//   ① KHÔNG quay màn đăng nhập — đăng nhập ngầm qua `/api/session`.
//   ② KHÔNG để mã OTP, huy hiệu DEVELOPMENT, hay nhãn dự án cũ "T121" vào khung.
//   ③ KHÔNG sửa một chữ nào trong lời agent. Cắt lượt được; sửa chữ thì không.
// ---------------------------------------------------------------------------

const MK_NHAN_VIEN = process.env.STAFF_PW;
const MK_KHACH = process.env.CUSTOMER_PW ?? "Demo@123";
if (!MK_NHAN_VIEN) throw new Error("STAFF_PW chưa đặt.");

const VE_DEMO = "TCK-839559b46901";
const VE_CHO_DUYET = "TCK-415f58704d99";
const CSKH = "0353000201";
const SEP = "0905000205";
const KHACH = "0974000145";

async function dangNhapNgam(page: Page, phone: string, mk: string) {
  const r = await page.request.post("/api/session", { data: { phone, password: mk } });
  expect(r.status(), `đăng nhập ${phone}`).toBe(200);
}

/** Dựng lớp phủ phụ đề + ẩn chân trang mang nhãn dự án CŨ ("T121", đã sửa
 *  thành "P-226" ở HEAD 25/08 — ngăn quay dựng TRƯỚC bản vá).
 *  Phải gọi lại SAU MỖI lần điều hướng: DOM bị dựng lại. */
async function dungKhung(page: Page) {
  await page.addStyleTag({
    content: `.foot{visibility:hidden !important}
      #pd{position:fixed;left:0;right:0;bottom:0;z-index:2147483647;
          background:linear-gradient(to top,rgba(10,11,16,.97),rgba(10,11,16,.88));
          color:#F2F4F8;font-family:"Source Sans 3",system-ui,sans-serif;font-size:21px;
          line-height:1.5;padding:20px 56px 24px;text-align:center;
          border-top:1px solid rgba(255,255,255,.10)}
      #pd b{color:#fff}`,
  }).catch(() => {});
  await page.evaluate(() => {
    if (!document.getElementById("pd")) {
      const d = document.createElement("div");
      d.id = "pd";
      document.body.appendChild(d);
    }
  }).catch(() => {});
}

/** Đặt phụ đề. Chuỗi rỗng = tắt. */
async function phuDe(page: Page, html: string) {
  await page.evaluate((h) => {
    const d = document.getElementById("pd");
    if (d) { d.innerHTML = h; (d as HTMLElement).style.display = h ? "block" : "none"; }
  }, html).catch(() => {});
}

async function cuonCham(page: Page, tong: number, buoc: number, nghi: number) {
  const b = Math.round(tong / buoc);
  for (let i = 0; i < buoc; i++) { await page.mouse.wheel(0, b); await page.waitForTimeout(nghi); }
}

/** Khung chữ nền trơn — dùng cho cảnh 02 và câu chốt cảnh 05. */
async function khungChu(page: Page, than: string, giay: number) {
  await page.setContent(`<html lang="vi"><head><meta charset="utf-8"><style>
    @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&display=swap');
    html,body{margin:0;height:100%}
    body{background:#0E0F15;color:#EAECF2;display:flex;align-items:center;justify-content:center;
         font-family:"Source Sans 3",system-ui,sans-serif}
    .b{max-width:880px;padding:0 56px;line-height:1.62;font-size:26px}
    .ma{font-family:ui-monospace,monospace;color:#9FB4FF;font-size:23px}
    .n{display:block;margin-top:28px;padding-top:24px;border-top:1px solid #262A38;
       font-size:22px;color:#AEB4C6}
  </style></head><body><div class="b">${than}</div></body></html>`);
  await page.waitForTimeout(giay);
}

test("video-180s-lien-mach", async ({ page }) => {
  const loiAgent = (hoiThoai as { vai: string; noi_dung: string }[]).filter((m) => m.vai === "ai").map((m) => m.noi_dung);
  const loiKhach = (hoiThoai as { vai: string; noi_dung: string }[]).filter((m) => m.vai === "human").map((m) => m.noi_dung);

  let luot = 0;
  await page.route("**/api/agent-chat", async (route) => {
    const reply = loiAgent[Math.min(luot++, loiAgent.length - 1)];
    await new Promise((r) => setTimeout(r, 850));
    await route.fulfill({ status: 200, contentType: "application/json",
      body: JSON.stringify({ reply, tool_calls: [], ly_do_fallback: null }) });
  });

  // ══ CẢNH 00 · 14s — VIỆC ĐANG LÀM BẰNG TAY ══════════════════════════════
  await dangNhapNgam(page, CSKH, MK_NHAN_VIEN!);
  await page.goto("/dashboard");
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 140); // đẩy huy hiệu DEVELOPMENT ra khỏi khung
  await phuDe(page, "Mỗi khiếu nại bắt đầu bằng việc tìm đúng một giao dịch giữa hàng loạt giao dịch giống hệt nhau.");
  await page.waitForTimeout(10_500);
  await phuDe(page, "Đó là số phút làm việc của nhân viên, nhân với số khiếu nại mỗi ngày.");
  await cuonCham(page, 380, 5, 1_500);

  // ══ CẢNH 01 · 44s — KHÁCH NÓI, AGENT TÌM RA KIM ═════════════════════════
  await dangNhapNgam(page, KHACH, MK_KHACH);
  await page.goto("/chat");
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 135);
  await phuDe(page, "Khách mô tả bằng lời thường. Agent tra bằng công cụ thật — không ra thì nói chưa ra rồi hỏi thêm, không đoán.");
  await page.waitForTimeout(3_000);

  const o = page.getByRole("textbox").last();
  const pd = [
    "Khách mô tả bằng lời thường. Agent tra bằng công cụ thật — không ra thì nói chưa ra rồi hỏi thêm, không đoán.",
    "Khách chỉ nhớ mang máng: cuối tháng 7, khoảng bảy rưỡi tối, ba trăm ba chín nghìn…",
    "…hệ thống trả về <b>một mã giao dịch xác định</b>.",
    "Khách đòi biết người nhận là ai.",
    "Nó từ chối: <b>dữ liệu người thứ ba được che ngay trên đường đi.</b>",
  ];
  for (let i = 0; i < loiKhach.length; i++) {
    await phuDe(page, pd[Math.min(i, pd.length - 1)]);
    await o.click({ timeout: 5_000 }).catch(() => {});
    await o.fill(loiKhach[i]).catch(() => {});
    await page.waitForTimeout(600);
    await page.keyboard.press("Enter");
    await page.waitForTimeout(i === 2 || i === 4 ? 6_800 : 5_000);
  }
  await page.waitForTimeout(3_000);

  // ══ CẢNH 02 · 10s — KHAI BẢN DỰNG LẠI ═══════════════════════════════════
  await khungChu(page,
    `Dựng lại từ phiên thật, mã <span class="ma">USR-0145:1787651345</span> — không viết lại câu nào.
     <span class="n"><b>61 giây</b>: thời gian hệ thống do công cụ đo bắn gõ, chưa phải người dùng thật.</span>`,
    10_000);

  // ══ CẢNH 03 · 36s — CẢNH GIÁ TRỊ ════════════════════════════════════════
  await dangNhapNgam(page, CSKH, MK_NHAN_VIEN!);
  await page.goto(`/tickets/${VE_DEMO}`);
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 130);
  await phuDe(page, "Nhân viên không nhận một lời than. Họ nhận một hồ sơ đã điều tra: đúng giao dịch, đã phân loại, năm bước tra cứu ghi lại được.");
  await page.waitForTimeout(6_000);
  await phuDe(page, "Đồng hồ xử lý đã chạy từ lúc tiếp nhận. Việc còn lại của họ là quyết định — không phải đi tìm.");
  await cuonCham(page, 560, 12, 1_500);
  await page.mouse.wheel(0, -260);
  await page.waitForTimeout(1_500);

  const nutKhoa = page.getByRole("button", { name: "Duyệt hoàn tiền" });
  await expect(nutKhoa).toBeDisabled(); // 🔴 nút CÓ, và bị KHOÁ — không phải "không có nút"
  await phuDe(page, "Nút duyệt hoàn tiền có ở đó. <b>Nó khoá với họ</b> — và sản phẩm nói thẳng vì sao.");
  await nutKhoa.hover({ force: true });
  await page.waitForTimeout(9_500);

  // ══ CẢNH 04 · 40s — NGƯỜI DUYỆT ═════════════════════════════════════════
  await dangNhapNgam(page, SEP, MK_NHAN_VIEN!);
  await page.goto("/approve");
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 130);
  await phuDe(page, "Người duyệt phải xác thực lại trong vòng 10 phút trước khi chạm vào tiền.");
  await page.waitForTimeout(5_000);
  // 🔴 CUỘN ÍT: chân bảng "Nhật ký hành động phê duyệt" in một câu SAI —
  // "Log không sửa/xoá được…" ([ĐO] 0 hash-chain/append-only/trigger). Không quay nó.
  await cuonCham(page, 230, 4, 1_600);
  await page.waitForTimeout(3_500);

  await page.goto(`/tickets/${VE_CHO_DUYET}`);
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 130);
  await phuDe(page, "Không ai vừa đề xuất vừa duyệt chính đề xuất của mình — hai vai, hai người.");
  await cuonCham(page, 300, 6, 1_500);
  await phuDe(page, "Ép ở tầng dữ liệu, <b>không phải ở quy trình nội bộ</b>. Viết thẳng câu lệnh vào cơ sở dữ liệu cũng bị từ chối.");
  await page.waitForTimeout(13_000);

  // ══ CẢNH 05 · 31s — KIỂM ĐƯỢC + HAI CÂU THẬT ════════════════════════════
  await page.goto(`/tickets/${VE_DEMO}`);
  await page.waitForLoadState("networkidle");
  await dungKhung(page);
  await page.mouse.wheel(0, 130);
  await phuDe(page, "Mọi con số agent nói ra đều gắn với một kết quả tra cứu có thật, mở ra kiểm được.");
  const ct = page.locator("summary", { hasText: "Xem dữ liệu kỹ thuật" }).first();
  if (await ct.count()) { await ct.click().catch(() => {}); }
  await page.waitForTimeout(6_000);
  await phuDe(page, "Tra không ra thì nó nói là không tra được.");
  await cuonCham(page, 260, 4, 1_500);
  await page.waitForTimeout(2_000);

  await khungChu(page,
    `Hai điều chúng tôi <b>chưa</b> chứng minh được:
     <span class="n">sản phẩm chưa chạy trên lưu lượng thật, và trải nghiệm người dùng thì chưa ai đo.</span>`,
    20_000);
});
