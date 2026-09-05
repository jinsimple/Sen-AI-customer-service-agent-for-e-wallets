import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import CskhOnlineClient from "./CskhOnlineClient";

export default async function CskhOnlinePage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <CskhOnlineClient />;
}
