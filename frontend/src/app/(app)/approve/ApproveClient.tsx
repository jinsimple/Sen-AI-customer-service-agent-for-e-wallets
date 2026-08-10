"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ApiError, approveResolution, listResolutions, rejectResolution } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, SCOPE_LABEL, type ResolutionListItem } from "@/lib/types";
import { formatDateTime, formatMoney } from "@/lib/format";

export default function ApproveClient() {
  const [pending, setPending] = useState<ResolutionListItem[] | null>(null);
  const [history, setHistory] = useState<ResolutionListItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

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
    load();
  }, []);

  async function handleApprove(id: string) {
    setBusyId(id);
    try {
      await approveResolution(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Duyệt thất bại");
    } finally {
      setBusyId(null);
    }
  }

  async function handleReject(id: string) {
    setBusyId(id);
    try {
      await rejectResolution(id);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Từ chối thất bại");
    } finally {
      setBusyId(null);
    }
  }

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

            <div className="flex gap-sm wrap" style={{ marginTop: 16 }}>
              <button className="btn btn-success" disabled={busyId === r.resolution_id} onClick={() => handleApprove(r.resolution_id)}>
                <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg>
                Duyệt
              </button>
              <button className="btn btn-danger-outline" disabled={busyId === r.resolution_id} onClick={() => handleReject(r.resolution_id)}>
                <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" /></svg>
                Từ chối
              </button>
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
