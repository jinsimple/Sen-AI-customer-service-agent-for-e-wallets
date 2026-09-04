import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// ADR-064(b) — "Nhận vé" chủ động, không body (POST /tickets/{id}/claim
// backend chỉ cần ticket_id qua path + current_user qua token).
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
