import { test, expect, type Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// KỊCH BẢN QUAY VIDEO TRÌNH SẢN PHẨM — 6 cảnh, 180 giây.
// Đặc tả từng nhịp: phiếu quay FIN-05 §3.
//
// 🔴 TỆP NÀY DO **PO** VIẾT — xem đầu `playwright.quay-video.config.ts`.
//
// HAI LUẬT CỨNG CỦA BUỔI QUAY, vi phạm là hỏng cả cảnh:
//   ① KHÔNG quay màn hình đăng nhập. Đăng nhập chạy NGẦM qua `/api/session`
//      để lấy cookie phiên — trình duyệt không bao giờ hiện form đăng nhập.
//      (Ngăn này dựng trước khi cổng chặn-sai-cổng land: `/dang-nhap-noi-bo`
//      307 về `/login`, nên quay màn đó là quay một luồng KHÁC sản phẩm hiện tại.)
//   ② KHÔNG để MÃ OTP lọt vào khung hình ở cảnh 04. Quay cận ô nhập và dòng
//      "còn hiệu lực 10 phút", không lấy chỗ hiện mã.
// ---------------------------------------------------------------------------

const MK_NHAN_VIEN = process.env.STAFF_PW;
const MK_KHACH = process.env.CUSTOMER_PW ?? "Demo@123";

// Fail-fast, không có giá trị mặc định cho mật khẩu nhân viên (12-factor).
if (!MK_NHAN_VIEN) {
  throw new Error(
    "STAFF_PW chưa đặt. Chạy: STAFF_PW='<mật khẩu nhân viên ngăn fin05-dot-otp>' npx playwright test --config=playwright.quay-video.config.ts"
  );
}

const VE_DEMO = "TCK-839559b46901"; // wrong_recipient · internal_wallet · TXN20260728000108 · 5 bước điều tra
const CSKH = "0353000201"; // Hồ Xuân Anh
const SEP = "0905000205"; // Phan Hữu Châu
const KHACH = "0974000145"; // USR-0145 — khách trong hội thoại được dựng lại

/** Đăng nhập NGẦM — không qua giao diện, không lọt khung hình.
 *  `page.request` dùng chung kho cookie với BrowserContext, nên cookie httpOnly
 *  do BFF đặt sẽ theo sang mọi `page.goto()` sau đó. */
async function dangNhapNgam(page: Page, phone: string, matKhau: string) {
  const res = await page.request.post("/api/session", {
    data: { phone, password: matKhau },
  });
  expect(res.status(), `đăng nhập ${phone} phải thành công`).toBe(200);
}

/** Cuộn chậm để người xem đọc kịp — quay chậm là CHỦ ĐÍCH, không phải chậm chạp. */
async function cuonCham(page: Page, tongPx: number, soBuoc: number, nghiMs: number) {
  const buoc = Math.round(tongPx / soBuoc);
  for (let i = 0; i < soBuoc; i++) {
    await page.mouse.wheel(0, buoc);
    await page.waitForTimeout(nghiMs);
  }
}


/** Ẩn chân trang trước khi quay.
 *  🔴 KHAI RÕ, vì đây là ranh giới mỏng: chân trang bản dựng này in mã dự án
 *  CŨ "T121". Mã đó ĐÃ ĐƯỢC SỬA thành "P-226" ở HEAD từ 25/08
 *  (`app/(app)/layout.tsx`) — ngăn quay chỉ dựng TRƯỚC bản vá.
 *  ⟹ Ta KHÔNG che một sự thật; ta bỏ khỏi khung một NHÃN ĐÃ HỎNG mà sản phẩm
 *  hiện tại không còn mang. Phần tử này chỉ chứa nhãn dự án, KHÔNG chứa dữ
 *  liệu sản phẩm nào. Cùng loại với việc cuộn qua dải header — đóng khung,
 *  không sửa hình.
 *  Nếu quay lại trên một ngăn dựng từ HEAD, BỎ hàm này đi. */
async function anChanTrang(page: Page) {
  await page.addStyleTag({ content: ".foot{visibility:hidden !important}" }).catch(() => {});
}

// ===========================================================================
// CẢNH 03 · 01:12–01:52 · 40 giây — CẢNH GIÁ TRỊ
// "Nhân viên không nhận một lời than. Họ nhận một hồ sơ đã điều tra."
// ===========================================================================
test("canh-03-nhan-vien-mo-ve", async ({ page }) => {
  await dangNhapNgam(page, CSKH, MK_NHAN_VIEN!);

  await page.goto(`/tickets/${VE_DEMO}`);
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);

  // 🔴 ĐẨY HEADER RA KHỎI KHUNG NGAY. Dải trên mang huy hiệu
  // "DEVELOPMENT · postgresql/fin05" + tên người dùng — tiêu chí soát hình
  // của Marketing (câu 5) LOẠI mọi ảnh lộ huy hiệu môi trường.
  // Đây là ĐÓNG KHUNG, không phải sửa hình: ta không che gì, ta chỉ không
  // ngắm vào dải đó. Tiền lệ do Marketing lập cho ảnh landing 27/08.
  await page.mouse.wheel(0, 130);
  await page.waitForTimeout(3_500);

  // Quay chậm qua vùng có ĐỦ HAI CỘT: nhật ký điều tra bên trái (5 bước đã
  // ghi) và "Thông tin giao dịch" + "Hành động của bạn (CSKH)" bên phải.
  // 🔴 KHÔNG cuộn sâu: chân trang bản dựng này còn in mã dự án CŨ "T121"
  // (đã sửa thành "P-226" ở HEAD 25/08, nhưng ngăn quay dựng TRƯỚC bản vá).
  // Không cuộn tới đáy thì lỗi đó không bao giờ vào khung hình.
  await cuonCham(page, 560, 14, 1_600);

  // Về đúng chỗ ô "Hành động của bạn (CSKH)".
  await page.mouse.wheel(0, -260);
  await page.waitForTimeout(2_500);

  // 🔴 NHỊP MẠNH NHẤT CỦA CẢ VIDEO, và nó KHÁC thứ phiếu quay bản 1 mô tả.
  // Bản 1 viết "màn hình của họ KHÔNG CÓ nút duyệt" — SAI. [ĐO 28/08]
  // `TicketDetailClient.tsx:433` render nút "Duyệt hoàn tiền" CÓ thuộc tính
  // `disabled`, bọc trong tooltip "Ngoài thẩm quyền của bạn — chỉ Sếp mới có
  // quyền duyệt hoàn tiền."
  // Nút HIỆN RA rồi bị KHOÁ mạnh hơn nút vắng mặt: vắng mặt đọc được thành
  // "thiếu tính năng", còn khoá kèm lý do là TỪ CHỐI CÓ CHỦ ĐÍCH.
  const nutDuyet = page.getByRole("button", { name: "Duyệt hoàn tiền" });
  await expect(nutDuyet).toBeDisabled();
  await nutDuyet.hover({ force: true }); // `force` vì nút disabled không nhận trỏ
  await page.waitForTimeout(5_500); // giữ khung cho người xem đọc hết tooltip
});

// ===========================================================================
// CẢNH 00 · 00:00–00:14 · 14 giây — VIỆC ĐANG LÀM BẰNG TAY
// "Mỗi khiếu nại bắt đầu bằng việc tìm đúng một giao dịch giữa hàng loạt
//  giao dịch giống hệt nhau. Đó là số phút làm việc của nhân viên, nhân với
//  số khiếu nại mỗi ngày."
// ===========================================================================
test("canh-00-viec-lam-bang-tay", async ({ page }) => {
  await dangNhapNgam(page, CSKH, MK_NHAN_VIEN!);
  await page.goto("/dashboard"); // hàng chờ vé — `/tickets` là 404 trên bản dựng này
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);

  // Đẩy header (huy hiệu DEVELOPMENT) ra khỏi khung ngay.
  await page.mouse.wheel(0, 140);
  await page.waitForTimeout(4_000); // khung tĩnh: để người xem tự thấy đống rơm

  // Cuộn RẤT chậm, ngắn — đủ để thấy hàng chờ dài, không đi đâu cả.
  await cuonCham(page, 420, 6, 1_500);
});

// ===========================================================================
// CẢNH 02 · 01:02–01:12 · 10 giây — KHAI BẢN DỰNG LẠI
// Khung chữ, nền trơn. KHÔNG phải giao diện sản phẩm.
// ===========================================================================
test("canh-02-khai-ban-dung-lai", async ({ page }) => {
  await page.setContent(`
    <html lang="vi"><head><meta charset="utf-8"><style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&display=swap');
      html,body{margin:0;height:100%}
      body{background:#12131A;color:#E8EAF0;display:flex;align-items:center;justify-content:center;
           font-family:"Source Sans 3",system-ui,sans-serif}
      .box{max-width:820px;padding:0 48px;line-height:1.65;font-size:26px}
      .ma{font-family:ui-monospace,monospace;color:#9FB4FF;font-size:23px}
      .nho{display:block;margin-top:26px;font-size:22px;color:#A8AEBF}
    </style></head><body><div class="box">
      Dựng lại từ phiên thật, mã <span class="ma">USR-0145:1787651345</span> — không viết lại câu nào.
      <span class="nho"><b>61 giây</b>: thời gian hệ thống do công cụ đo bắn gõ, chưa phải người dùng thật.</span>
    </div></body></html>`);
  await page.waitForTimeout(10_000); // 10 giây đứng yên, đúng ngân sách đọc
});

// ===========================================================================
// CẢNH 04 · 01:52–02:28 · 36 giây — NGƯỜI DUYỆT
// 🔴 MÃ OTP KHÔNG ĐƯỢC LÊN HÌNH.
// ===========================================================================
test("canh-04-nguoi-duyet", async ({ page }) => {
  await dangNhapNgam(page, SEP, MK_NHAN_VIEN!);
  await page.goto("/approve");
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);

  await page.mouse.wheel(0, 130); // header ra khỏi khung
  await page.waitForTimeout(4_000);

  // 🔴 CUỘN ÍT — DỪNG TRÊN "Nhật ký hành động phê duyệt".
  // [ĐO 28/08] chân bảng đó in nguyên văn: "Log không sửa/xoá được bởi người
  // dùng thường — tra cứu được theo ticket_id." (`ApproveClient.tsx:127`).
  // Câu đó SAI: [ĐO] 0 hash-chain, 0 append-only, 0 trigger trong `src/` và
  // `migrations/`. Đây chính là một trong BỐN câu sai đã biết của bộ slide
  // (STATE §0.7c) — đội đi sửa slide và không ai kiểm sản phẩm có nói câu đó
  // không. Nó vẫn ở HEAD.
  // Không quay nó. Không phải để giấu — mà vì quay một câu SAI lên video trình
  // đối tác là nhân bản lỗi, không phải ghi lại sự thật.
  await cuonCham(page, 230, 5, 1_700);
  await page.waitForTimeout(4_500); // giữ khung ở hai đề xuất đang chờ + Căn cứ

  // 🔴 NHỊP ĐẮT NHẤT CỦA CẢNH: mở ĐÚNG cái ô mà CSKH vừa bị khoá ở cảnh 03,
  // lần này bằng vai SẾP. Cùng một màn hình, cùng một nút — khác vai, khác
  // trạng thái. Đó là bằng chứng bằng MẮT cho "hai vai, hai người", mạnh hơn
  // mọi câu chữ ta viết được.
  // Đi thẳng bằng URL, KHÔNG bấm "Mở chi tiết": cú bấm đó không điều hướng
  // ([ĐO 28/08]) và cuộn tiếp sau đó làm lộ dòng sai + chân trang T121.
  await page.goto("/tickets/TCK-415f58704d99");
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);
  await page.mouse.wheel(0, 130); // header ra khỏi khung
  await page.waitForTimeout(3_500);
  await cuonCham(page, 300, 8, 1_400); // 🔴 KHÔNG quá 300px: hơn nữa là chân trang "T121" (mã dự án CŨ) vào khung

  const nutDuyetSep = page.getByRole("button", { name: "Duyệt hoàn tiền" });
  if (await nutDuyetSep.count()) {
    await nutDuyetSep.hover({ force: true }).catch(() => {});
  }
  await page.waitForTimeout(6_000); // giữ khung trên ô hành động của SẾP
});

// ===========================================================================
// CẢNH 05 · 02:28–03:00 · 32 giây — KIỂM ĐƯỢC + HAI CÂU THẬT
// ===========================================================================
test("canh-05-kiem-duoc-va-hai-cau-that", async ({ page }) => {
  await dangNhapNgam(page, CSKH, MK_NHAN_VIEN!);
  await page.goto(`/tickets/${VE_DEMO}`);
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);
  await page.mouse.wheel(0, 130);
  await page.waitForTimeout(2_500);

  // Mở một thẻ "Xem dữ liệu kỹ thuật" — chỗ con số trỏ về kết quả tool có thật.
  const chiTiet = page.locator("summary", { hasText: "Xem dữ liệu kỹ thuật" }).first();
  if (await chiTiet.count()) {
    await chiTiet.click().catch(() => {});
    await page.waitForTimeout(5_000);
  }
  await cuonCham(page, 300, 4, 1_500);
  await page.waitForTimeout(2_000);

  // Khung chữ cuối — nền trơn, không giao diện.
  await page.setContent(`
    <html lang="vi"><head><meta charset="utf-8"><style>
      @import url('https://fonts.googleapis.com/css2?family=Source+Sans+3:wght@400;600&display=swap');
      html,body{margin:0;height:100%}
      body{background:#12131A;color:#E8EAF0;display:flex;align-items:center;justify-content:center;
           font-family:"Source Sans 3",system-ui,sans-serif}
      .box{max-width:860px;padding:0 48px;line-height:1.6;font-size:25px}
      .hai{display:block;margin-top:30px;padding-top:24px;border-top:1px solid #2C2F3C;color:#C6CBD8}
    </style></head><body><div class="box">
      Mọi con số agent nói ra đều gắn với một kết quả tra cứu có thật, mở ra kiểm được.
      Tra không ra thì nó nói là không tra được.
      <span class="hai">Hai điều chúng tôi <b>chưa</b> chứng minh được: sản phẩm chưa chạy trên lưu lượng thật,
      và trải nghiệm người dùng thì chưa ai đo.</span>
    </div></body></html>`);
  await page.waitForTimeout(14_000);
});

// ===========================================================================
// CẢNH 01 · 00:14–01:02 · 48 giây — KHÁCH NÓI MỘT CÂU, AGENT TÌM RA KIM
// 🔴 DỰNG LẠI: chặn lời gọi mạng, trả NGUYÊN VĂN phản hồi từ bản ghi thật
//    (thread USR-0145:1787651345, 28 lượt → gói còn 10 nhịp).
//    KHÔNG sửa một chữ nào trong câu của agent. Cắt lượt thì được, sửa chữ thì không.
// 🔴 ĐÃ CẮT nhịp cuối của bản gốc — nhịp đó nêu hạn xử lý "24/09" (30 ngày).
//    Ghép một con số 30 ngày vào ngay sau khi video nói "61 giây" là tự đặt
//    mâu thuẫn cạnh chính luận điểm của mình (luật Marketing nêu cho khối S3
//    trang landing). Cắt lượt là hợp lệ; sửa lời agent thì không.
// ===========================================================================
import hoiThoai from "./quay-video.hoithoai.json";

test("canh-01-khach-noi-agent-tim-ra-kim", async ({ page }) => {
  const loiAgent = (hoiThoai as { vai: string; noi_dung: string }[])
    .filter((m) => m.vai === "ai")
    .map((m) => m.noi_dung);
  const loiKhach = (hoiThoai as { vai: string; noi_dung: string }[])
    .filter((m) => m.vai === "human")
    .map((m) => m.noi_dung);

  let luot = 0;
  await page.route("**/api/agent-chat", async (route) => {
    const reply = loiAgent[Math.min(luot, loiAgent.length - 1)];
    luot += 1;
    // Giữ nhịp "agent đang nghĩ" cho thật — nhưng NÉN lại: bản ghi gốc mất
    // 61 giây cho cả phiên, ta có 48 giây cho 10 nhịp.
    await new Promise((r) => setTimeout(r, 900));
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ reply, tool_calls: [], ly_do_fallback: null }),
    });
  });

  await dangNhapNgam(page, KHACH, MK_KHACH);
  await page.goto("/chat");
  await page.waitForLoadState("networkidle");
  await anChanTrang(page);
  // Đẩy header (huy hiệu DEVELOPMENT + tên khách) ra khỏi khung, như mọi cảnh khác.
  await page.mouse.wheel(0, 135);
  await page.waitForTimeout(3_000);

  const o = page.getByRole("textbox").last();
  for (let i = 0; i < loiKhach.length; i++) {
    await o.click({ timeout: 5_000 }).catch(() => {});
    await o.fill(loiKhach[i]).catch(() => {});
    await page.waitForTimeout(700);
    await page.keyboard.press("Enter");
    // Đợi câu trả lời hiện ra rồi mới gõ tiếp — nhịp của người thật.
    await page.waitForTimeout(i === 2 || i === 4 ? 7_000 : 5_000);
  }
  await page.waitForTimeout(7_000); // giữ khung ở câu chốt
});
