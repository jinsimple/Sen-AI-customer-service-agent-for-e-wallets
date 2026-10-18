"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { roleHome, type Role } from "@/lib/session";
import { useI18n } from "@/lib/i18n/client";

// Shared by /login (customer) and /dang-nhap-noi-bo (support/supervisor/partner) — split the PAGE,
// not the MECHANISM (PO decision, Aug 26). Both call the same endpoint; the role always comes from
// the server's RESPONSE looked up by phone — no parameter here decides what PERMISSIONS the user
// gets.
//
// `gate` (Aug 26, PO reversed the earlier "just let them in" call) is a deliberate, narrow
// EXCEPTION: it can ONLY make a login FAIL FURTHER (route /api/session compares the role the server
// returned against the gate and rejects on a mismatch — see route.ts), never help it succeed
// further or change which role is granted. It is not the "parameter that decides permissions" the
// project banned (Aug 12) — that would be a parameter that OPENS permissions; this one only CLOSES.
// Sending the wrong `gate` can't route around anything, it can only get the sender rejected.
export function useLoginForm(gate: "customer" | "internal") {
  const router = useRouter();
  const { t } = useI18n();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function doLogin(loginPhone: string, loginPassword: string) {
    setError(null);
    setLoading(true);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10_000);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: loginPhone.trim(), password: loginPassword, gate }),
        signal: controller.signal,
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail ?? t("login.errWrong"));
        return;
      }
      router.push(roleHome(body.role as Role));
      router.refresh();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError(t("login.errTimeout"));
      } else {
        setError(t("login.errNetwork"));
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await doLogin(phone, password);
  }

  return { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit };
}
