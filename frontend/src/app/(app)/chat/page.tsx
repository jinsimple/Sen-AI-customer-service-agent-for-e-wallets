import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import ChatClient from "./ChatClient";

export default async function ChatPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <ChatClient userId={session.user_id} phone={session.phone} />;
}
