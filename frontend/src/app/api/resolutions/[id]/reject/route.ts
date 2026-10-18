import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { id } = await params;
  // ADR-019 — the body must carry `reason`; this route previously didn't read the body, so it must
  // be forwarded, or the backend always gets a 422 for the missing field.
  const body = await req.json();
  try {
    const data = await backendFetch(
      `/resolutions/${encodeURIComponent(id)}/reject`,
      session.access_token,
      { method: "POST", body: JSON.stringify(body) }
    );
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
