import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import { roleHome } from "@/lib/session";

// proxy.ts đã redirect "/" trước khi tới đây trong đa số trường hợp — trang
// này là lớp phòng thủ thứ hai (docs Next.js khuyến nghị không chỉ dựa vào
// proxy cho auth), phòng khi có đường vào không qua proxy.
export default async function Home() {
  const session = await getServerSession();
  redirect(session ? roleHome(session.role) : "/login");
}
