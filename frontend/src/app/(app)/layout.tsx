import Link from "next/link";
import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import TopbarActions from "@/components/TopbarActions";
import RoleTabNav from "@/components/RoleTabNav";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession();
  if (!session) redirect("/login");

  return (
    <div className="app">
      <header className="topbar">
        <Link href="/" className="brand">
          <div className="brand-mark">S</div>
          {/* 26/08 — bỏ phụ đề "FIN-05 · AI Agent xử lý khiếu nại giao dịch":
              đó là câu quảng cáo, người ĐÃ đăng nhập không cần nghe lại ở
              mọi trang, mọi lượt — thuộc landing, không thuộc khung app. */}
          <div className="brand-text">
            <b>Sen — Trợ lý CSKH ví điện tử</b>
          </div>
        </Link>
        <TopbarActions fullName={session.full_name} role={session.role} />
      </header>
      <RoleTabNav role={session.role} />
      <main>{children}</main>
      {/* 🔴 "T121" -> "P-226" (25/08). Đây KHÔNG phải sửa chính tả: chuỗi này in
          trên MỌI TRANG sản phẩm, tức thứ KHÁCH HÀNG nhìn thấy, và PO sắp chia sẻ
          công khai. PO thật đã ra lệnh sửa mã dự án cùng ngày — cả đội đi sửa TÀI
          LIỆU và không ai sửa chỗ này. Mã đúng: P-226 (khớp git remote, xem
          CLAUDE.md §8: dòng ghi P-121 là SAI, đã đính chính 18/08). */}
      <footer className="foot">FIN-05 · P-226 — AI 20K Build Phase Cohort 3</footer>
    </div>
  );
}
