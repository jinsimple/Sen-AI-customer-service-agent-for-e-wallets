"use client";

import { roleHome, type Role } from "@/lib/session";

// UI-02 — băng báo LỆCH VAI.
//
// Bug PO gặp giữa demo mentor: đăng nhập CSKH trong CÙNG trình duyệt đè phiên
// khách (kiến trúc BFF cố ý dùng MỘT cookie phiên). Tab chat khách vẫn mở, gõ
// tiếp -> `/agent/chat` trả 403 `"Cần role thuộc ['customer'], tài khoản hiện
// tại là cskh"` -> câu đó rơi thẳng vào khung chat dưới dạng "Có lỗi: …" giữa
// buổi demo.
//
// VÌ SAO VÁ Ở CLIENT chứ không ở guard route: `proxy.ts` CÓ chặn theo vai
// (`ROLE_PREFIXES`) và redirect đúng — nhưng nó chỉ chạy khi có ĐIỀU HƯỚNG.
// Tab đang mở không điều hướng lần nào; 403 tới từ lời gọi API. Guard route
// không bao giờ nhìn thấy ca này.
//
// KHÔNG đổi cơ chế phiên: một-cookie-một-phiên là thiết kế BFF có chủ đích
// (token không bao giờ rời server, trình duyệt chỉ giữ cookie httpOnly). Việc
// của bản vá là biến một lỗi khó hiểu thành một hướng dẫn — không phải cho
// phép hai vai cùng sống trong một trình duyệt.

const TEN_VAI: Record<string, string> = {
  customer: "Khách hàng",
  cskh: "Nhân viên CSKH",
  supervisor: "Cấp duyệt",
  partner_admin: "Đối tác ví",
};

export default function BannerLechVai({
  vaiHienTai,
  vaiCanCo,
}: {
  vaiHienTai: string;
  vaiCanCo: string;
}) {
  const ten = TEN_VAI[vaiHienTai] ?? vaiHienTai;
  const tenCan = TEN_VAI[vaiCanCo] ?? vaiCanCo;
  const ve = roleHome(vaiHienTai as Role);

  return (
    <div
      role="alert"
      style={{
        border: "1px solid var(--warn-border, #d9a441)",
        background: "var(--warn-bg, #fff8e6)",
        color: "var(--warn-fg, #6b4b00)",
        borderRadius: 8,
        padding: "12px 14px",
        margin: "10px 0",
        fontSize: 14,
        lineHeight: 1.6,
      }}
    >
      <strong>Bạn đang đăng nhập bằng tài khoản {ten}.</strong>
      <div style={{ marginTop: 4 }}>
        Màn hình này dành cho <strong>{tenCan}</strong>. Nhiều khả năng bạn vừa đăng nhập
        vai khác ở một tab khác trong cùng trình duyệt — mỗi trình duyệt chỉ giữ được
        một phiên.
      </div>
      <div style={{ marginTop: 6 }}>
        Muốn dùng song song hai vai: mở <strong>cửa sổ ẩn danh</strong> cho vai thứ hai.
      </div>
      <a href={ve} style={{ display: "inline-block", marginTop: 10, fontWeight: 600 }}>
        → Về màn hình của {ten}
      </a>
    </div>
  );
}
