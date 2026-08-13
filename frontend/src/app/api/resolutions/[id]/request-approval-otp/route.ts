import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// AUTH5-04 (đợt nâng cấp Auth Flow 2026-08-12) — sếp xin OTP RIÊNG cho đúng
// resolution_id này trước khi nút "Duyệt" hoạt động được (xem
// TicketDetailClient.tsx). otp_code trả thẳng ở đây CHỈ vì đây là môi
// trường demo (backend không gửi SMS thật) — cùng cách /api/otp/request đã
// làm cho luồng khách hàng.
export async function POST(_req: Request, { params }: { params: Promise<{ id: string }> }) {
  const session = await getServerSession();
  if (!session) return unauthorized();

  const { id } = await params;
  try {
    const data = await backendFetch(
      `/resolutions/${encodeURIComponent(id)}/request-approval-otp`,
      session.access_token,
      { method: "POST" }
    );
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
