import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import TicketDetailClient from "./TicketDetailClient";

export default async function TicketDetailPage({ params }: PageProps<"/tickets/[id]">) {
  const session = await getServerSession();
  if (!session) redirect("/login");
  const { id } = await params;
  return <TicketDetailClient ticketId={id} viewerRole={session.role} />;
}
