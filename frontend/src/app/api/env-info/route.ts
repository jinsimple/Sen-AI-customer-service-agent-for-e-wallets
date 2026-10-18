import { NextResponse } from "next/server";

/**
 * Environment identity (Aug 13, 2026) — reports which BACKEND and which DATABASE this stack is
 * talking to.
 *
 * Born from a real incident: the Docker stack (Caddy :80 → Postgres) and the local dev stack (next
 * dev :3000 → uvicorn :8010 → SQLite) were running side by side. Two IDENTICAL-LOOKING browser
 * windows but different databases — the customer's ticket went into Postgres, the support agent
 * read from SQLite and permanently saw 0. See ADR-009.
 *
 * No login required: it only returns the scheme + DB name (no host/user/password), and must be
 * visible right on the /login screen — exactly when the user needs to know which backend they're
 * logging into.
 */
export async function GET() {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8010";
  try {
    const res = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) throw new Error(`backend trả ${res.status}`);
    const data = (await res.json()) as { env?: string; db_kind?: string; db_name?: string; build_commit?: string; build_at?: string };
    return NextResponse.json({
      env: data.env ?? "unknown",
      db_kind: data.db_kind ?? "unknown",
      db_name: data.db_name ?? "unknown",
      // A fingerprint — lets you ask, FROM OUTSIDE, which build production is running.
      build_commit: data.build_commit ?? "khong-ro",
      build_at: data.build_at ?? "khong-ro",
      backend: backendUrl,
    });
  } catch {
    // Don't let an error bubble up to the UI — the environment label is supporting information;
    // breaking it must NOT break the page. Return an "unknown" state so the badge shows a warning
    // instead of silently disappearing (disappearing would be exactly the invisible-environment
    // problem this mechanism exists to block).
    return NextResponse.json({
      env: "unreachable",
      db_kind: "unknown",
      db_name: "unknown",
      // Can't reach the backend ⟹ we DON'T KNOW which build it is — say "not-determined", never
      // guess using the value from the previous call.
      build_commit: "khong-ro",
      build_at: "khong-ro",
      backend: backendUrl,
    });
  }
}
