"use client";

import { useEffect, useState } from "react";
import { useI18n } from "@/lib/i18n/client";

/**
 * Environment-identity label — shown in the topbar AND on the login screen.
 *
 * WHY THIS FILE EXISTS (read carefully before "tidying up the UI" by removing it):
 * on 2026-08-13, the Docker stack (port 80 → Postgres) and the local dev stack (port 3000 → SQLite)
 * were running side by side. The PO had a customer window open at `localhost` and a support-agent
 * window at `localhost:3000`. The two UIs looked IDENTICAL but were two different systems with two
 * different databases: the customer's ticket went into Postgres, the support agent read from SQLite
 * and permanently saw 0 tickets, no amount of refreshing helped. Hours of investigation while every
 * layer of code was correct.
 *
 * This label makes the environment SELF-DECLARE: look and know, instead of inferring it from the
 * port number in the address bar. Two windows with different labels = you immediately know you're
 * looking at two different stacks, no investigation needed.
 *
 * The label HIDES ITSELF when `env === "production"` — real users don't need to see it.
 *
 * [Sep 3, ADR-060] `NEXT_PUBLIC_HIDE_ENV_BADGE` — a SEPARATE build-time flag, off by default, same
 * pattern as `NEXT_PUBLIC_QUICK_LOGIN`. Why a new flag instead of changing `APP_ENV`: the badge and
 * the fail-fast guard in `config.py:199` both read the EXACT same `APP_ENV` variable, so changing
 * `APP_ENV` to enable OTP_DEMO_MODE for the Scene 6 video shoot would make the badge REAPPEAR —
 * exactly what needs hiding. This flag separates the two concerns without touching `config.py`.
 * Production leaves the flag unset ⟹ identical old behaviour, no regression.
 */

type EnvInfo = { env: string; db_kind: string; db_name: string; backend: string };

const MAU: Record<string, { nen: string; chu: string }> = {
  production: { nen: "#0F2A1B", chu: "#7EE2A8" },
  docker: { nen: "#12304D", chu: "#8BC4F0" },
  development: { nen: "#3A2410", chu: "#F0C078" },
  unreachable: { nen: "#3A1414", chu: "#F09595" },
};

export default function EnvBadge({ compact = false }: { compact?: boolean }) {
  const [info, setInfo] = useState<EnvInfo | null>(null);
  const { t } = useI18n();

  useEffect(() => {
    fetch("/api/env-info", { cache: "no-store" })
      .then((r) => r.json())
      .then(setInfo)
      .catch(() => {});
  }, []);

  if (!info) return null;
  if (info.env === "production") return null;
  if (process.env.NEXT_PUBLIC_HIDE_ENV_BADGE === "true") return null;

  const mau = MAU[info.env] ?? MAU.development;
  const khongKetNoi = info.env === "unreachable";

  // Short label, but ENOUGH to tell the two stacks apart: DB kind + DB name. `sqlite/app.db` vs
  // `postgresql/fin05` — recognisable at a glance.
  const nhan = khongKetNoi
    ? t("env.unreachable")
    : `${info.env.toUpperCase()} · ${info.db_kind}/${info.db_name}`;

  return (
    <span
      title={
        khongKetNoi
          ? t("env.unreachableTitle", { backend: info.backend })
          : t("env.title", { env: info.env, kind: info.db_kind, name: info.db_name, backend: info.backend })
      }
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        background: mau.nen,
        color: mau.chu,
        border: `1px solid ${mau.chu}55`,
        padding: compact ? "4px 9px" : "6px 11px",
        borderRadius: 999,
        fontSize: compact ? 11 : 11.5,
        fontWeight: 700,
        letterSpacing: ".02em",
        whiteSpace: "nowrap",
        cursor: "help",
      }}
    >
      <span
        style={{
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: mau.chu,
          flex: "none",
        }}
      />
      {nhan}
    </span>
  );
}
