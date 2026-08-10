import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// Proxy thẳng /auth/otp/request (backend) — không cần cập nhật cookie ở đây
// (chưa có gì đổi về danh tính, chỉ mới xin mã OTP). access_token vẫn ở lại
// server, route này chỉ chuyển tiếp phần công khai (otp_code mô phỏng, câu
// hỏi bảo mật) cho client hiển thị.
export async function POST() {
  const session = await getServerSession();
  if (!session) return unauthorized();

  try {
    const data = await backendFetch("/auth/otp/request", session.access_token, { method: "POST" });
    return NextResponse.json(data);
  } catch (e) {
    return proxyErrorResponse(e);
  }
}
