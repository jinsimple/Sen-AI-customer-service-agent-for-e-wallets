import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// ADR-064(b) — an active "claim ticket" with no body (POST /tickets/{id}/claim on the backend only
// needs the ticket_id via the path and current_user via the token).
export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { id } = await params;
  try {
    const data = await backendFetch(`/tickets/${encodeURIComponent(id)}/claim`, session.access_token, {
      method: "POST",
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
