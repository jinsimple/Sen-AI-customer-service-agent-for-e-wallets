import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { message } = await req.json();
  try {
    const data = await backendFetch("/agent/chat", session.access_token, {
      method: "POST",
      body: JSON.stringify({ message }),
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
