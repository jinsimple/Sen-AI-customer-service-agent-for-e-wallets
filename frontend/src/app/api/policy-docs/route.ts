import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function GET() {
  const session = await getServerSession();
  if (!session) return unauthorized();

  try {
    const data = await backendFetch("/policy-docs", session.access_token, { method: "GET" });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}

export async function POST(req: Request) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  // Receive multipart from the browser and forward the FormData AS-IS to FastAPI — don't read/parse
  // the file content at this layer (backendFetch drops the default Content-Type itself when the
  // body is FormData, see lib/server-api.ts).
  const formData = await req.formData();
  try {
    const data = await backendFetch("/policy-docs", session.access_token, {
      method: "POST",
      body: formData,
    });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
