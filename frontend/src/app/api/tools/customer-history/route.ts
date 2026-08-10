import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const body = await req.json();
  try {
    const data = await backendFetch("/tools/get_customer_history", session.access_token, {
      method: "POST",
      body: JSON.stringify(body),
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
