import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import { LAST_GATE_COOKIE, loginPathForGate } from "@/lib/session";
import TopbarActions from "@/components/TopbarActions";
import RoleTabNav from "@/components/RoleTabNav";
import { getT } from "@/lib/i18n/server";

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession();
  const { t } = await getT();
  // Same patch as the "logout dead end" in proxy.ts — in the normal flow, proxy already blocks
  // before reaching here; this is a second line of defence so behaviour doesn't drift if the proxy
  // matcher changes later. See lib/session.ts::LAST_GATE_COOKIE.
  if (!session) {
    const goiY = (await cookies()).get(LAST_GATE_COOKIE)?.value;
    redirect(loginPathForGate(goiY));
  }

  return (
    <div className="app">
      <header className="topbar">
        <Link href="/" className="brand">
          <div className="brand-mark">S</div>
          {/* 26/08 — bỏ phụ đề "FIN-05 · AI Agent xử lý khiếu nại giao dịch":
              đó là câu quảng cáo, người ĐÃ đăng nhập không cần nghe lại ở
              mọi trang, mọi lượt — thuộc landing, không thuộc khung app. */}
          <div className="brand-text">
            <b>{t("app.brand")}</b>
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
      <footer className="foot">{t("app.footer")}</footer>
    </div>
  );
}
