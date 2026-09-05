"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ApiError, getPolicyDoc } from "@/lib/api";
import type { PolicyDocFullText } from "@/lib/types";

// ADR-065 (05/09) — deep-link "Xem toàn văn" từ /policy-lookup, mở TAB MỚI.
// Tự cuộn + tô sáng đúng đoạn đã khớp khi có `chunk_id` — tài liệu 1 đoạn
// (FAQ ngắn) hiện thẳng toàn văn, không cần cuộn (đoạn tô sáng = gần hết
// trang, scrollIntoView vẫn chạy đúng, chỉ không có gì để cuộn tới thêm).
export default function PolicyDocPage() {
  const { docId } = useParams<{ docId: string }>();
  const searchParams = useSearchParams();
  const chunkId = searchParams.get("chunk_id") ?? undefined;

  const [doc, setDoc] = useState<PolicyDocFullText | null>(null);
  const [error, setError] = useState<string | null>(null);
  const highlightRef = useRef<HTMLElement>(null);

  useEffect(() => {
    getPolicyDoc(docId, chunkId)
      .then(setDoc)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Không tải được tài liệu"));
  }, [docId, chunkId]);

  useEffect(() => {
    if (doc?.highlight) {
      highlightRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [doc]);

  if (error) {
    return (
      <div className="page-head">
        <h1>Không mở được tài liệu</h1>
        <p className="sub">{error}</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="page-head">
        <p className="sub">Đang tải…</p>
      </div>
    );
  }

  if (doc.full_text === null) {
    return (
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH · Tài liệu chính sách</span>
        <h1>{doc.filename}</h1>
        <p className="sub">
          Tài liệu này chưa có bản toàn văn để hiển thị — vui lòng dùng đoạn trích ở kết quả tra cứu.
        </p>
      </div>
    );
  }

  const { full_text, highlight } = doc;
  const before = highlight ? full_text.slice(0, highlight.start) : full_text;
  const marked = highlight ? full_text.slice(highlight.start, highlight.end) : "";
  const after = highlight ? full_text.slice(highlight.end) : "";

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH · Tài liệu chính sách</span>
        <h1 className="mono" style={{ fontSize: 20 }}>{doc.filename}</h1>
        <p className="sub">Toàn văn tài liệu — đoạn trích khớp câu tra cứu được tô sáng bên dưới, nếu có.</p>
      </div>

      <div className="card" style={{ whiteSpace: "pre-wrap", lineHeight: 1.7 }}>
        {before}
        {highlight && (
          <mark
            ref={highlightRef}
            style={{ background: "var(--warning-bg)", color: "var(--warning)", borderRadius: 4, padding: "1px 2px" }}
          >
            {marked}
          </mark>
        )}
        {after}
      </div>
    </>
  );
}
