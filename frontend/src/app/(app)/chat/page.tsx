import { redirect } from "next/navigation";
import { getOtpXemConHan, getServerSession } from "@/lib/session-server";
import ChatClient from "./ChatClient";

export default async function ChatPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  // Finding A (phase 2.5 / M-10) — compute the OTP expiry in ONE place (the server), hand the
  // client exactly one derived boolean, and never carry the access_token/claim out.
  return <ChatClient userId={session.user_id} phone={session.phone} otpXemConHanLucTai={getOtpXemConHan(session)} />;
}
