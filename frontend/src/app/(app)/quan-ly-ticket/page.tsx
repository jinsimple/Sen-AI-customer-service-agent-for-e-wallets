import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import QuanLyTicketClient from "./QuanLyTicketClient";

export default async function QuanLyTicketPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <QuanLyTicketClient />;
}
