import { NextResponse } from "next/server";
import { getServerSession } from "@/lib/session-server";
import { backendFetch, proxyErrorResponse, unauthorized } from "@/lib/server-api";

// Plain proxy to /auth/otp/request (backend) — no cookie update needed here (nothing about identity
// changes yet, this is just requesting an OTP). access_token stays on the server; this route only
// forwards the public part (simulated otp_code, security question) for the client to display.
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
