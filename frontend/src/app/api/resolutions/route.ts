import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function GET(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { search } = new URL(req.url);
  try {
    const data = await backendFetch(`/resolutions${search}`, session.access_token, { method: "GET" });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
