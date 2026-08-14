import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

export async function POST(req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { id } = await params;
  // ADR-019 — body mang `reason` bắt buộc; route này trước đây không đọc body
  // nên phải chuyển tiếp, nếu không backend luôn nhận 422 thiếu trường.
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
