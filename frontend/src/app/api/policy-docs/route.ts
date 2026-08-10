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

  // Nhận multipart từ trình duyệt rồi forward NGUYÊN FormData sang FastAPI —
  // không đọc/parse lại nội dung file ở tầng này (backendFetch tự bỏ
  // Content-Type mặc định khi thấy body là FormData, xem lib/server-api.ts).
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
