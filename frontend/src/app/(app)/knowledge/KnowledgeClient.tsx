"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, deletePolicyDoc, listPolicyDocs, uploadPolicyDoc } from "@/lib/api";
import type { PolicyDocument } from "@/lib/types";
import { formatDateTime } from "@/lib/format";

const STATUS_LABEL: Record<PolicyDocument["status"], string> = {
  processing: "Đang xử lý",
  indexed: "Đã lập chỉ mục",
  failed: "Lỗi",
};

const STATUS_BADGE: Record<PolicyDocument["status"], string> = {
  processing: "badge-warning",
  indexed: "badge-success",
  failed: "badge-danger",
};

export default function KnowledgeClient() {
  const [docs, setDocs] = useState<PolicyDocument[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [busyId, setBusyId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function load() {
    setError(null);
    try {
      setDocs(await listPolicyDocs());
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Không tải được danh sách tài liệu");
    }
  }

  useEffect(() => {
    void Promise.resolve().then(load);
  }, []);

  async function handleUpload(e: React.FormEvent) {
    e.preventDefault();
    const file = fileInputRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      await uploadPolicyDoc(file);
      if (fileInputRef.current) fileInputRef.current.value = "";
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Upload thất bại");
    } finally {
      setUploading(false);
    }
  }

  async function handleDelete(docId: string) {
    setBusyId(docId);
    try {
      await deletePolicyDoc(docId);
      await load();
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Xoá thất bại");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp Đối tác ví · RAG chính sách/FAQ</span>
        <h1>Chính sách & FAQ</h1>
        <p className="sub">
          Tài liệu tải lên ở đây được AI agent dùng để trả lời khách hàng và giúp CSKH tra cứu nhanh —
          hỗ trợ .md/.txt/.pdf/.docx (không hỗ trợ .doc cũ). Nội dung được mã hoá khi lưu trữ.
        </p>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="card">
        <div className="card-title">Tải tài liệu mới</div>
        <form onSubmit={handleUpload} className="flex gap-sm wrap center-y" style={{ marginTop: 12 }}>
          <input ref={fileInputRef} type="file" accept=".md,.txt,.pdf,.docx" required />
          <button className="btn btn-gold" type="submit" disabled={uploading}>
            {uploading ? "Đang tải lên…" : "Tải lên"}
          </button>
        </form>
      </div>

      <div className="section" style={{ marginTop: 30 }}>
        <div className="section-title">Tài liệu đã tải lên</div>
        <div className="card scroll-x" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Tên file</th>
                <th>Người tải lên</th>
                <th>Thời gian</th>
                <th>Trạng thái</th>
                <th>Số đoạn</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {docs?.map((d) => (
                <tr key={d.doc_id}>
                  <td>{d.filename}</td>
                  <td>{d.uploaded_by_name ?? "—"}</td>
                  <td className="mono" style={{ fontSize: 12 }}>{formatDateTime(d.uploaded_at)}</td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[d.status]}`}>{STATUS_LABEL[d.status]}</span>
                    {d.status === "failed" && d.error_message && (
                      <div className="dim" style={{ fontSize: 11, marginTop: 4 }}>{d.error_message}</div>
                    )}
                  </td>
                  <td>{d.chunk_count}</td>
                  <td>
                    <button
                      className="btn btn-danger-outline btn-sm"
                      disabled={busyId === d.doc_id}
                      onClick={() => handleDelete(d.doc_id)}
                    >
                      Xoá
                    </button>
                  </td>
                </tr>
              ))}
              {docs?.length === 0 && (
                <tr>
                  <td colSpan={6} className="dim" style={{ textAlign: "center", padding: 20 }}>
                    Chưa có tài liệu nào.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </>
  );
}
