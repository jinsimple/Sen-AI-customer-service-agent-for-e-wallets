import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function GET() {
  const session = await getServerSession();
  if (!session) return unauthorized();

  try {
    const data = await backendFetch("/notifications", session.access_token, { method: "GET" });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
