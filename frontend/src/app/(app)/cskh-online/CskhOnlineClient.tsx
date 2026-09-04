"use client";

import StaffPresenceTable from "@/components/StaffPresenceTable";

// [04/09] Tách khỏi trang Phê duyệt sang tab riêng — PO đo thật: đông CSKH
// làm bảng chật chỗ trang duyệt. Bảng + cơ chế presence/heartbeat giữ
// NGUYÊN (StaffPresenceTable.tsx), đây chỉ đổi CHỖ hiển thị.
export default function CskhOnlineClient() {
  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp Sếp</span>
        <h1>CSKH online</h1>
        <p className="sub">
          Ai đang online và đang xử lý bao nhiêu vé — để biết phân bổ việc, không phải để chấm công.
        </p>
      </div>

      <StaffPresenceTable />
    </>
  );
}
