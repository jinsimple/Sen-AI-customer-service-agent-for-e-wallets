import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function GET(_req: Request, { params }: { params: Promise<{ ticketId: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { ticketId } = await params;
  try {
    const data = await backendFetch(`/live-chat/sessions/by-ticket/${encodeURIComponent(ticketId)}`, session.access_token, {
      method: "GET",
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
