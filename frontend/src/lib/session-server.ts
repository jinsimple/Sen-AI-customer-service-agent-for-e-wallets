import "server-only";
import { cookies } from "next/headers";
import { parseSessionCookie, SESSION_COOKIE, type Session } from "@/lib/session";

export async function getServerSession(): Promise<Session | null> {
  const store = await cookies();
  return parseSessionCookie(store.get(SESSION_COOKIE)?.value);
}
