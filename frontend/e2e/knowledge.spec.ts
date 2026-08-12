import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/knowledge` (Webapp Đối tác ví, RAG chính
 * sách/FAQ) chưa có e2e nào. Upload/xoá tài liệu THẬT qua UI — ingest
 * (src/rag/ingest.py::ingest_document) chạy ĐỒNG BỘ trong cùng request (kể
 * cả bước lập chỉ mục vector), nên KHÔNG cần polling: form submit xong là
 * đã có status "indexed"/"failed" ngay.
 */
const PARTNER_ADMIN_PHONE = "0900000001";

test.describe("KNOWLEDGE-* — tải/xoá tài liệu chính sách", () => {
  test("tải lên file .txt hợp lệ -> hiện 'Đã lập chỉ mục' với số đoạn > 0, xoá xong biến mất khỏi bảng", async ({ page }) => {
    await loginAs(page, PARTNER_ADMIN_PHONE, "Đối tác ví (Chính sách)", "/knowledge");

    const filename = `e2e-test-policy-${Date.now()}.txt`;
    await page.setInputFiles('input[type="file"]', {
      name: filename,
      mimeType: "text/plain",
      buffer: Buffer.from(
        "Chính sách hoàn tiền: Với giao dịch bị trừ tiền 2 lần do lỗi hệ thống, ví hoàn tiền trong vòng 3 ngày làm việc sau khi CSKH xác nhận."
      ),
    });
    await page.getByRole("button", { name: "Tải lên" }).click();

    const row = page.locator("tbody tr", { hasText: filename });
    await expect(row).toBeVisible({ timeout: 20_000 });
    await expect(row.locator(".badge-success")).toHaveText("Đã lập chỉ mục");
    // Cột "Số đoạn" (chunk_count) — phải > 0, không phải 0 (bằng chứng tách
    // đoạn/lập chỉ mục thật sự chạy, không chỉ đổi status cho có).
    const chunkCountText = await row.locator("td").nth(4).textContent();
    expect(Number(chunkCountText)).toBeGreaterThan(0);

    await row.getByRole("button", { name: "Xoá" }).click();
    await expect(row).not.toBeVisible({ timeout: 10_000 });
  });

  test("tải lên file rỗng -> báo lỗi rõ ràng, KHÔNG thêm dòng nào vào bảng", async ({ page }) => {
    await loginAs(page, PARTNER_ADMIN_PHONE, "Đối tác ví (Chính sách)", "/knowledge");

    // Phát hiện thật: đếm hàng NGAY sau khi điều hướng bị đếm hụt (0) — bảng
    // tải danh sách bất đồng bộ (KnowledgeClient.tsx::load(), gọi qua
    // Promise.resolve().then), đếm quá sớm bắt trúng lúc bảng còn rỗng vì
    // CHƯA load xong, không phải vì thật sự chưa có tài liệu nào. Chờ 1 trong
    // 2 trạng thái ổn định (có hàng HOẶC placeholder "chưa có tài liệu") rồi
    // mới đếm baseline.
    await Promise.race([
      page.locator("tbody tr").first().waitFor({ state: "visible", timeout: 10_000 }),
      page.getByText("Chưa có tài liệu nào.").waitFor({ state: "visible", timeout: 10_000 }),
    ]);
    const rowsBefore = await page.locator("tbody tr").count();

    const filename = `e2e-empty-${Date.now()}.txt`;
    await page.setInputFiles('input[type="file"]', {
      name: filename,
      mimeType: "text/plain",
      buffer: Buffer.from(""),
    });
    await page.getByRole("button", { name: "Tải lên" }).click();

    await expect(page.locator(".note", { hasText: /rỗng|thất bại/i })).toBeVisible({ timeout: 10_000 });
    const rowsAfter = await page.locator("tbody tr").count();
    expect(rowsAfter).toBe(rowsBefore);
  });
});
