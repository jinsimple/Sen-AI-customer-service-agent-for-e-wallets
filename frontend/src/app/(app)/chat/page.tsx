import { redirect } from "next/navigation";
import { getOtpXemConHan, getServerSession } from "@/lib/session-server";
import ChatClient from "./ChatClient";

export default async function ChatPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  // Finding A (GĐ2.5 / M-10) — tính hạn OTP MỘT NƠI (server), truyền xuống
  // client đúng một boolean đã dẫn xuất, KHÔNG bê access_token/claim ra ngoài.
  return <ChatClient userId={session.user_id} phone={session.phone} otpXemConHanLucTai={getOtpXemConHan(session)} />;
}
