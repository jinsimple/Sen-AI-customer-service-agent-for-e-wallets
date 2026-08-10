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
          <div className="brand-text">
            <b>Sen — Trợ lý CSKH ví điện tử</b>
            <span>FIN-05 · AI Agent xử lý khiếu nại giao dịch</span>
          </div>
        </Link>
        <TopbarActions fullName={session.full_name} role={session.role} />
      </header>
      <RoleTabNav role={session.role} />
      <main>{children}</main>
      <footer className="foot">FIN-05 · T121 — AI 20K Build Phase Cohort 3</footer>
    </div>
  );
}
