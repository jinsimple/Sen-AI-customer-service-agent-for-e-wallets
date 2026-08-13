import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { id } = await params;
  // AUTH5-04 — session_id/otp_code bắt buộc, xin qua POST
  // .../request-approval-otp trước (xem TicketDetailClient.tsx).
  const { session_id, otp_code } = await req.json();
  try {
    const data = await backendFetch(
      `/resolutions/${encodeURIComponent(id)}/approve`,
      session.access_token,
      { method: "POST", body: JSON.stringify({ session_id, otp_code }) }
    );
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
