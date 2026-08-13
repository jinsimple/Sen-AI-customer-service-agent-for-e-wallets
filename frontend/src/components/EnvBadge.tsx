"use client";

import { useEffect, useState } from "react";

/**
 * Nhãn định danh môi trường — hiện ở topbar VÀ ở màn hình đăng nhập.
 *
 * VÌ SAO CÓ FILE NÀY (đọc kỹ trước khi định gỡ cho "gọn giao diện"):
 * ngày 2026-08-13, Docker stack (cổng 80 → Postgres) và stack dev cục bộ
 * (cổng 3000 → SQLite) chạy song song. PO mở cửa sổ khách ở `localhost` và
 * cửa sổ CSKH ở `localhost:3000`. Hai giao diện GIỐNG HỆT NHAU nhưng là hai
 * hệ thống khác nhau với hai database khác nhau: khách tạo ticket vào
 * Postgres, CSKH đọc từ SQLite nên vĩnh viễn thấy 0 ticket, F5 bao nhiêu lần
 * cũng vô ích. Mất nhiều giờ điều tra trong khi mọi tầng code đều đúng.
 *
 * Nhãn này làm cho môi trường TỰ KHAI BÁO: nhìn là biết, không phải suy luận
 * từ số cổng trên thanh địa chỉ. Hai cửa sổ khác nhãn = biết ngay đang lệch
 * stack, không cần điều tra.
 *
 * Nhãn TỰ ẨN khi `env === "production"` — người dùng thật không cần thấy.
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

  useEffect(() => {
    fetch("/api/env-info", { cache: "no-store" })
      .then((r) => r.json())
      .then(setInfo)
      .catch(() => {});
  }, []);

  if (!info) return null;
  if (info.env === "production") return null;

  const mau = MAU[info.env] ?? MAU.development;
  const khongKetNoi = info.env === "unreachable";

  // Nhãn ngắn gọn nhưng ĐỦ để phân biệt 2 stack: loại DB + tên DB.
  // `sqlite/app.db` vs `postgresql/fin05` — nhìn phát biết ngay.
  const nhan = khongKetNoi
    ? "KHÔNG NỐI ĐƯỢC BACKEND"
    : `${info.env.toUpperCase()} · ${info.db_kind}/${info.db_name}`;

  return (
    <span
      title={
        khongKetNoi
          ? `Không gọi được ${info.backend}/health — kiểm tra backend đã chạy chưa.`
          : `Môi trường: ${info.env}\nDatabase: ${info.db_kind} / ${info.db_name}\nBackend: ${info.backend}\n\n` +
            "Hai cửa sổ trình duyệt PHẢI hiện cùng một nhãn. Khác nhãn = đang ở hai " +
            "hệ thống khác nhau với hai database khác nhau (xem ADR-009)."
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
