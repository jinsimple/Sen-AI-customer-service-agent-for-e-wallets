"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, listResolutions } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, SCOPE_LABEL, type ResolutionListItem } from "@/lib/types";
import { formatDateTime, formatMoney } from "@/lib/format";

export default function ApproveClient() {
  const [pending, setPending] = useState<ResolutionListItem[] | null>(null);
  const [history, setHistory] = useState<ResolutionListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    try {
      const [p, all] = await Promise.all([listResolutions("pending_approval"), listResolutions("all")]);
      setPending(p);
      setHistory(all.filter((r) => r.status === "approved" || r.status === "rejected"));
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không tải được hàng chờ phê duyệt");
    }
  }

  useEffect(() => {
    // Không gọi load() trực tiếp — load() setState (setError) ĐỒNG BỘ ở
    // dòng đầu tiên (trước await nào), react-hooks/set-state-in-effect coi
    // đó là setState đồng bộ trong effect. Đẩy lời gọi ra khỏi lượt đồng bộ
    // hiện tại (microtask) — đúng tinh thần .then()-chain dashboard/page.tsx
    // đã dùng, nhưng vẫn giữ được load() dạng async/await tái dùng ở nơi
    // khác (handleApprove...).
    void Promise.resolve().then(load);
  }, []);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp Sếp · US-005, US-017</span>
        <h1>Phê duyệt (HITL)</h1>
        <p className="sub">
          Đủ căn cứ hiển thị ngay để quyết trong vài giây. Case chạm ngân hàng chỉ có nút tạo yêu cầu tra
          soát — không bao giờ có đường tắt bỏ qua con người.
        </p>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="grid grid-2" style={{ alignItems: "start" }}>
        {pending?.length === 0 && <div className="dim">Không có đề xuất nào đang chờ duyệt.</div>}
        {pending?.map((r) => (
          <div className="card" key={r.resolution_id}>
            <div className="flex between center-y" style={{ marginBottom: 6 }}>
              <Link href={`/tickets/${r.ticket_id}`} className="card-title mono" style={{ fontSize: 15 }}>
                {r.ticket_id}
              </Link>
              <span className="badge badge-neutral">
                {r.scope === "internal_wallet" ? "Nội bộ ví — đủ quyền thực thi trực tiếp" : "Chạm ngân hàng — chờ đối tác xác nhận"}
              </span>
            </div>
            <div className="card-sub">
              {r.complaint_type ? COMPLAINT_TYPE_LABEL[r.complaint_type] : "—"}
              {r.scope ? ` · ${SCOPE_LABEL[r.scope]}` : ""}
            </div>
            <div className="kv-row" style={{ marginTop: 12 }}>
              <span className="k">Đề xuất từ CSKH</span>
              <span className="v">{r.action_type}{r.amount ? ` — ${formatMoney(r.amount)}` : ""}</span>
            </div>
            <div className="kv-row"><span className="k">Căn cứ</span><span className="v" style={{ fontWeight: 400 }}>{r.rationale}</span></div>
            <div className="kv-row"><span className="k">Trình lúc</span><span className="v" style={{ fontWeight: 400 }}>{formatDateTime(r.created_at)}</span></div>

            {r.scope && r.scope !== "internal_wallet" ? (
              <div className="note callout-gold" style={{ marginTop: 12 }}>
                Case chạm ngân hàng: quyết định duyệt ở đây ghi log căn cứ, CSKH là người gửi yêu cầu tra
                soát riêng (xem chi tiết ticket).
              </div>
            ) : null}

            {/* Hotfix 2 (14/08): trang này giờ CHỈ là hàng chờ tóm tắt — nút
                duyệt/từ chối đã chuyển vào chi tiết ticket, nơi có dấu vết điều
                tra và thông tin giao dịch. Để nút ở đây là mời sếp quyết mà không
                cần đọc căn cứ, ngược với US-005. */}
            <div className="flex gap-sm wrap" style={{ marginTop: 16 }}>
              <Link className="btn btn-primary" href={`/tickets/${r.ticket_id}`}>
                Mở chi tiết →
              </Link>
            </div>
          </div>
        ))}
      </div>

      <div className="section" style={{ marginTop: 30 }}>
        <div className="section-title">
          Nhật ký hành động HITL <span className="tag">US-017</span>
        </div>
        <div className="card">
          <div className="scroll-x">
            <table className="table">
              <thead>
                <tr><th>Thời gian</th><th>Ai</th><th>Hành động</th><th>Ticket</th><th>Căn cứ</th></tr>
              </thead>
              <tbody>
                {history?.map((r) => (
                  <tr key={r.resolution_id}>
                    <td className="mono" style={{ fontSize: 12 }}>{r.approved_at ? formatDateTime(r.approved_at) : "—"}</td>
                    <td>{r.approved_by_name ?? "—"}</td>
                    <td>
                      {r.status === "approved" ? (
                        <span className="badge badge-success">Duyệt</span>
                      ) : (
                        <span className="badge badge-danger">Từ chối</span>
                      )}
                    </td>
                    <td className="mono">
                      <Link href={`/tickets/${r.ticket_id}`}>{r.ticket_id}</Link>
                    </td>
                    <td className="dim" style={{ fontSize: 12 }}>{r.rationale}</td>
                  </tr>
                ))}
                {history?.length === 0 && (
                  <tr><td colSpan={5} className="dim" style={{ textAlign: "center", padding: 20 }}>Chưa có hành động nào.</td></tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="note" style={{ marginTop: 12 }}>
            <svg className="icon" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            <div>Log không sửa/xoá được bởi người dùng thường — tra cứu được theo ticket_id.</div>
          </div>
        </div>
      </div>
    </>
  );
}
