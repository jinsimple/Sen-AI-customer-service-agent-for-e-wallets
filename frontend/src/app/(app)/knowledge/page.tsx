import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import KnowledgeClient from "./KnowledgeClient";

export default async function KnowledgePage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <KnowledgeClient />;
}
