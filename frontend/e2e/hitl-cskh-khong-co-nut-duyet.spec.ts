import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * GĐ2 (docs/giao-viec/2026-08-19-gd2-envelope-null-va-e2e-ui.md) — ca thứ 3
 * của ma trận "luồng duyệt (cskh/supervisor)", tìm ra lúc khảo sát e2e/ hiện
 * có: approve.spec.ts đã phủ (a) supervisor duyệt, (b) supervisor từ chối —
 * cả hai khác NHÁNH quyết định. Ca này khác TRỤC hẳn: PHỦ ĐỊNH THẨM QUYỀN.
 *
 * PRD §2 US-012: "CSKH không có nút 'duyệt' cho bất kỳ case nào — chỉ có
 * 'trình sếp' / 'yêu cầu điều tra thêm'." Đúng ràng buộc cứng 1 (CLAUDE.md
 * §2.1): không tồn tại đường nào cho CSKH tự thực thi hoàn tiền/điều chỉnh
 * số dư. ticket-detail.spec.ts đã test 2 nút CSKH CÓ ("Trình sếp", "Yêu cầu
 * điều tra thêm") nhưng chưa ai assert nút CSKH KHÔNG CÓ — một cổng chỉ có
 * ca dương không phân biệt được "thẩm quyền đúng" với "form ẩn nút vì lý do
 * khác" (vd lỗi CSS, thiếu quyền tải component).
 *
 * 0 TOKEN — dùng ticket ĐÃ CÓ SẴN trong dashboard (seed demo + ticket sinh
 * từ các đợt E2E trước đó trong ngày), không tạo ticket mới qua AI.
 */
const CSKH_PHONE = "0353000201";

test.describe("HITL-* — GĐ2: phủ định thẩm quyền CSKH (US-012)", () => {
  test("CSKH mở một ticket bất kỳ -> KHÔNG có nút 'Duyệt' ở đâu trên trang", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const ticketId = (await rows.first().locator("td").first().textContent())?.trim();
    expect(ticketId).toMatch(/^TCK-/);

    await rows.first().click();
    await page.waitForURL(`**/tickets/${ticketId}`, { timeout: 10_000 });
    await expect(page.locator("h2.mono")).toHaveText(ticketId!);

    // Đợi trang render xong phần "Hành động của bạn (CSKH)" trước khi kết
    // luận vắng mặt — vắng mặt vì CHƯA LOAD XONG và vắng mặt vì THẨM QUYỀN
    // là hai điều khác nhau (cùng lỗi mà knowledge.spec.ts từng ghi nhận:
    // đếm quá sớm lúc bảng còn rỗng ra baseline sai).
    await Promise.race([
      page.getByRole("button", { name: "Trình sếp" }).waitFor({ state: "visible", timeout: 15_000 }).catch(() => null),
      page.getByRole("button", { name: "Yêu cầu điều tra thêm" }).waitFor({ state: "visible", timeout: 15_000 }).catch(() => null),
      page.getByText("Đã trình sếp — chờ phê duyệt.").waitFor({ state: "visible", timeout: 15_000 }).catch(() => null),
    ]);

    // Quét TOÀN TRANG (không giới hạn vùng), khớp CHÍNH XÁC nhãn "Duyệt" —
    // không dùng regex /duyệt/ lỏng: chuỗi "Đã trình sếp — chờ phê duyệt."
    // hoặc rationale CSKH gõ tự do có thể chứa chuỗi con trùng, khớp nhầm
    // (đúng bẫy approve.spec.ts đã ghi nhận cho badge "Từ chối").
    const nutDuyet = page.getByRole("button", { name: "Duyệt", exact: true });
    await expect(nutDuyet).toHaveCount(0);

    // Đối chứng: xác nhận trang THẬT SỰ đã render xong phần hành động (một
    // trong ba trạng thái ở trên phải có mặt) — nếu không, "0 nút Duyệt" có
    // thể chỉ vì cả trang chưa load, không phải vì thẩm quyền đúng.
    // Promise.race trả về cái ĐẦU TIÊN SETTLE, không phải cái đầu tiên TRUE
    // — dùng Promise.all + some() để kiểm ĐỦ CẢ BA trước khi kết luận.
    const baTrangThai = await Promise.all([
      page.getByRole("button", { name: "Trình sếp" }).isVisible().catch(() => false),
      page.getByRole("button", { name: "Yêu cầu điều tra thêm" }).isVisible().catch(() => false),
      page.getByText("Đã trình sếp — chờ phê duyệt.").isVisible().catch(() => false),
    ]);
    const coTrangThaiHanhDong = baTrangThai.some(Boolean);
    expect(
      coTrangThaiHanhDong,
      "Trang ticket-detail không render được TRẠNG THÁI HÀNH ĐỘNG nào (không 'Trình sếp', không " +
        "'Yêu cầu điều tra thêm', không 'Đã trình sếp') — '0 nút Duyệt' ở đây KHÔNG chứng minh được " +
        "gì về thẩm quyền, chỉ chứng minh trang chưa load."
    ).toBe(true);
  });
});
