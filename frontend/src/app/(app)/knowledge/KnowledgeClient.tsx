"use client";

import { useEffect, useRef, useState } from "react";
import { ApiError, deletePolicyDoc, listPolicyDocs, uploadPolicyDoc } from "@/lib/api";
import type { PolicyDocument } from "@/lib/types";
import { formatDateTime } from "@/lib/format";
import { useI18n } from "@/lib/i18n/client";
import type { DictKey } from "@/lib/i18n/dict";

const STATUS_LABEL: Record<PolicyDocument["status"], DictKey> = {
  processing: "kb.status.processing",
  indexed: "kb.status.indexed",
  failed: "kb.status.failed",
};

const STATUS_BADGE: Record<PolicyDocument["status"], string> = {
  processing: "badge-warning",
  indexed: "badge-success",
  failed: "badge-danger",
};

export default function KnowledgeClient() {
  const { t, lang } = useI18n();
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
      setError(e instanceof ApiError ? e.message : t("kb.loadError"));
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
      setError(e instanceof ApiError ? e.message : t("kb.uploadFailed"));
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
      setError(e instanceof ApiError ? e.message : t("kb.deleteFailed"));
    } finally {
      setBusyId(null);
    }
  }

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("kb.eyebrow")}</span>
        <h1>{t("kb.title")}</h1>
        <p className="sub">
          {t("kb.sub")}
        </p>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      <div className="card">
        <div className="card-title">{t("kb.uploadTitle")}</div>
        <form onSubmit={handleUpload} className="flex gap-sm wrap center-y" style={{ marginTop: 12 }}>
          <input ref={fileInputRef} type="file" accept=".md,.txt,.pdf,.docx" required />
          <button className="btn btn-gold" type="submit" disabled={uploading}>
            {uploading ? t("kb.uploading") : t("kb.upload")}
          </button>
        </form>
      </div>

      <div className="section" style={{ marginTop: 30 }}>
        <div className="section-title">{t("kb.listTitle")}</div>
        <div className="card scroll-x" style={{ padding: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th>{t("kb.colFile")}</th>
                <th>{t("kb.colUploader")}</th>
                <th>{t("kb.colTime")}</th>
                <th>{t("kb.colStatus")}</th>
                <th>{t("kb.colChunks")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {docs?.map((d) => (
                <tr key={d.doc_id}>
                  <td>{d.filename}</td>
                  <td>{d.uploaded_by_name ?? "—"}</td>
                  <td className="mono" style={{ fontSize: 12 }}>{formatDateTime(d.uploaded_at, lang)}</td>
                  <td>
                    <span className={`badge ${STATUS_BADGE[d.status]}`}>{t(STATUS_LABEL[d.status])}</span>
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
                      {t("kb.delete")}
                    </button>
                  </td>
                </tr>
              ))}
              {docs?.length === 0 && (
                <tr>
                  <td colSpan={6} className="dim" style={{ textAlign: "center", padding: 20 }}>
                    {t("kb.empty")}
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
