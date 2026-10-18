import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// ADR-065 (Sep 5) — deep-link that reads the full text for a /policy-search result.
export async function GET(req: Request, { params }: { params: Promise<{ docId: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { docId } = await params;
  const { search } = new URL(req.url);
  try {
    const data = await backendFetch(`/policy-doc/${encodeURIComponent(docId)}${search}`, session.access_token, {
      method: "GET",
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
