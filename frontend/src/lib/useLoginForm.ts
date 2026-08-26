"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { roleHome, type Role } from "@/lib/session";

// Dùng CHUNG cho /login (khách hàng) và /dang-nhap-noi-bo (CSKH/sếp/đối tác) —
// tách TRANG, không tách CƠ CHẾ (PO chốt 26/08). Cả hai gọi đúng một endpoint,
// vai trò luôn lấy từ RESPONSE server tra qua phone — không có tham số nào ở
// đây quyết định quyền người dùng nhận được. Nếu sau này cần khác biệt giữa
// hai trang, khác biệt đó phải nằm ở COPY/GIAO DIỆN của page, không phải ở hook này.
export function useLoginForm() {
  const router = useRouter();
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
        body: JSON.stringify({ phone: loginPhone.trim(), password: loginPassword }),
        signal: controller.signal,
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail ?? "Số điện thoại hoặc mật khẩu không đúng.");
        return;
      }
      router.push(roleHome(body.role as Role));
      router.refresh();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError("Máy chủ phản hồi quá lâu (>10s) — thử lại giúp mình nhé.");
      } else {
        setError("Không kết nối được máy chủ — kiểm tra backend đã chạy chưa (make run).");
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
