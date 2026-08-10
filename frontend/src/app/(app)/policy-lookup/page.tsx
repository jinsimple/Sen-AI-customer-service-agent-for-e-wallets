import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import PolicyLookupClient from "./PolicyLookupClient";

export default async function PolicyLookupPage() {
  const session = await getServerSession();
  if (!session) redirect("/login");
  return <PolicyLookupClient />;
}
