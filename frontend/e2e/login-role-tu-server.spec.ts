import { test, expect } from "@playwright/test";
import { DEMO_PASSWORD } from "./helpers/actors";

/**
 * [ĐO 26/08] login/page.tsx:57 — "Vai trò lấy từ RESPONSE của server, KHÔNG
 * phải lựa chọn" (quyết định bảo mật 12/08). Đăng nhập nội bộ (`/dang-nhap-
 * noi-bo`) đang được viết mới CÙNG LÚC, dùng chung `useLoginForm()` với
 * `/login` (khách hàng) — PO chốt 26/08: "tách TRANG, không tách CƠ CHẾ".
 *
 * Viết TỪ ĐẶC TẢ trên, KHÔNG đọc `src/` (backend, CLAUDE.md §4, tester cố ý
 * bị chặn đọc để không phản chiếu logic có sẵn — kể cả logic sai). Đây là
 * test HÀNH VI qua HTTP trực tiếp tới `/api/session` (đúng endpoint
 * `useLoginForm.ts` gọi, đọc được từ FRONTEND — không phải suy đoán): gửi
 * kèm một trường vai trò GIẢ MẠO trong body, và khẳng định vai trò NHẬN VỀ
 * vẫn là vai trò thật trong CSDL (tra qua `phone`), không phải vai trò đã
 * gửi lên.
 *
 * Không đi qua UI (không có ô chọn vai trò nào trên form thật — xác nhận qua
 * đọc `useLoginForm.ts`, hook chỉ gửi `{phone, password, gate}`) — kẻ tấn
 * công thật không cần UI, chỉ cần POST thẳng tới endpoint. Test qua UI sẽ
 * bỏ sót đúng đường tấn công này.
 *
 * 🔴 ĐÍNH CHÍNH 27/08 — sau khi tính năng chặn sai cổng (login-gate-tach-to-
 * chuc.spec.ts) land, `useLoginForm.ts` gửi thêm trường `gate: "customer" |
 * "internal"`. Request KHÔNG kèm `gate` giờ mặc định bị xử lý như cổng
 * "internal" (đo được: cùng SĐT khách hàng, request thiếu `gate` bị 403
 * "dùng cổng nhân viên" — dù chưa từng có gì hỏi tới role). Thiếu `gate:
 * "customer"` ở đây làm CẢ HAI ca mất tác dụng theo hai cách khác nhau: ca ①
 * (giả mạo role) vẫn "xanh" nhưng KHÔNG CÒN CHẠM tới logic gán role — bị
 * chặn bởi lớp gate TRƯỚC KHI tới đó, nên vòng `if (res.ok())` không chạy gì
 * cả (xanh rỗng); ca ② (đối chứng) đỏ thẳng vì lý do KHÔNG liên quan tới
 * điều nó test. Thêm `gate: "customer"` khớp đúng hành vi trang /login thật.
 */

const CUSTOMER_PHONE = "0387000001"; // USR-0001, role=customer thật trong dataset

test.describe("SEC — vai trò đăng nhập lấy từ server, không nhận trường gửi lên", () => {
  test("gửi kèm role='supervisor' giả mạo -> vẫn nhận về role thật (customer), KHÔNG phải role đã gửi", async ({
    page,
  }) => {
    const res = await page.request.post("/api/session", {
      data: {
        phone: CUSTOMER_PHONE,
        password: DEMO_PASSWORD,
        gate: "customer", // khớp đúng cổng thật của CUSTOMER_PHONE — xem đính chính 27/08 ở đầu file
        role: "supervisor", // 🔴 trường giả mạo — form thật không bao giờ gửi trường này
      },
    });

    // Hai kết cục AN TOÀN: (a) server bỏ qua trường lạ, xử lý bình thường,
    // trả role thật; (b) server từ chối thẳng request có trường lạ (4xx/5xx).
    // CHỈ MỘT kết cục là lỗ hổng: 200 kèm role == trường đã gửi (supervisor).
    if (res.ok()) {
      const body = await res.json();
      expect(
        body.role,
        `Server trả role='${body.role}' — KHỚP đúng role giả mạo đã gửi lên. ` +
          `Nếu role thật của ${CUSTOMER_PHONE} không phải 'supervisor', đây là lỗ ` +
          `leo thang quyền: bất kỳ ai có tài khoản khách + gửi thêm trường role đều ` +
          `tự phong được vai bất kỳ.`
      ).not.toBe("supervisor");
      expect(body.role, "Role nhận về phải là role THẬT trong CSDL (customer), không phải trường đã gửi.").toBe(
        "customer"
      );
    }
    // else: request bị từ chối thẳng (4xx/5xx) — cũng là kết cục an toàn, không assert gì thêm.
  });

  test("ca đối chứng — đăng nhập KHÔNG kèm trường role vẫn thành công bình thường, trả đúng role thật", async ({
    page,
  }) => {
    // 🔴 CA ĐỐI CHỨNG BẮT BUỘC (Luật A) — thiếu ca này, một bản vá kiểu "chặn
    // MỌI request có bất kỳ hình dạng nào" (vd luôn trả lỗi để 'né' ca trên)
    // cũng làm ca trên xanh, trong khi đăng nhập thật đã bị chặn theo.
    const res = await page.request.post("/api/session", {
      data: { phone: CUSTOMER_PHONE, password: DEMO_PASSWORD, gate: "customer" },
    });
    expect(res.ok(), `Đăng nhập hợp lệ (không trường lạ) phải thành công — status ${res.status()}`).toBe(true);
    const body = await res.json();
    expect(body.role).toBe("customer");
  });
});
