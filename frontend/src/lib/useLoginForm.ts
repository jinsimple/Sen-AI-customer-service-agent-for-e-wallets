"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { roleHome, type Role } from "@/lib/session";
import { useI18n } from "@/lib/i18n/client";

// Dùng CHUNG cho /login (khách hàng) và /dang-nhap-noi-bo (CSKH/sếp/đối tác) —
// tách TRANG, không tách CƠ CHẾ (PO chốt 26/08). Cả hai gọi đúng một endpoint,
// vai trò luôn lấy từ RESPONSE server tra qua phone — không có tham số nào ở
// đây quyết định QUYỀN người dùng nhận được.
//
// `gate` (26/08, PO đảo quyết định "cứ cho vào") là NGOẠI LỆ có chủ đích và
// hẹp: nó CHỈ có thể khiến đăng nhập THẤT BẠI THÊM (route /api/session so vai
// server trả về với gate, từ chối nếu lệch — xem route.ts), không bao giờ
// giúp thành công thêm hay đổi vai nhận được. Không phải "tham số quyết định
// quyền" mà dự án đã cấm (12/08) — đó là tham số MỞ quyền; đây là tham số chỉ
// ĐÓNG. Gửi sai `gate` không đi vòng qua được gì, chỉ tự làm mình bị từ chối.
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
