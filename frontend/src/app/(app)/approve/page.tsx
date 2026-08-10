import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import ApproveClient from "./ApproveClient";

export default async function ApprovePage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <ApproveClient />;
}
