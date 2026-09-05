"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ApiError, getPolicyDoc } from "@/lib/api";
import type { PolicyDocFullText } from "@/lib/types";
import { blockOverlapsHighlight, splitPolicyDocBlocks } from "@/lib/policyDocBlocks";

// ADR-065 (05/09) — deep-link "Xem toàn văn" từ /policy-lookup, mở TAB MỚI.
// Tự cuộn + tô sáng đúng đoạn đã khớp khi có `chunk_id` — tài liệu 1 đoạn
// (FAQ ngắn) hiện thẳng toàn văn, không cần cuộn (đoạn tô sáng = gần hết
// trang, scrollIntoView vẫn chạy đúng, chỉ không có gì để cuộn tới thêm).
//
// [polish 05/09, PO bắt qua ảnh chụp] `full_text` đọc thô từ docx: heading
// MỤC/ĐIỀU dính đuôi câu trước (không xuống dòng), đổ thẳng vào 1 khối
// `pre-wrap` làm cả trang thành MỘT đoạn văn phẳng. `splitPolicyDocBlocks`
// (lib/policyDocBlocks.ts) tách thành khối heading/url/đoạn văn — tô sáng
// đổi từ tô THEO KÝ TỰ sang tô THEO KHỐI giao với [highlight.start, end)
// (tự hết dính dòng luôn, vì mục dính đuôi giờ đã tách khối riêng).
export default function PolicyDocPage() {
  const { docId } = useParams<{ docId: string }>();
  const searchParams = useSearchParams();
  const chunkId = searchParams.get("chunk_id") ?? undefined;

  const [doc, setDoc] = useState<PolicyDocFullText | null>(null);
  const [error, setError] = useState<string | null>(null);
  const firstHighlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getPolicyDoc(docId, chunkId)
      .then(setDoc)
      .catch((e) => setError(e instanceof ApiError ? e.message : "Không tải được tài liệu"));
  }, [docId, chunkId]);

  const blocks = useMemo(() => {
    if (!doc?.full_text) return [];
    return splitPolicyDocBlocks(doc.full_text).filter((b) => b.type !== "blank");
  }, [doc]);

  // Chỉ số khối tô sáng ĐẦU TIÊN — tính TRƯỚC lúc render (không mutate biến
  // trong lúc .map(), React Compiler coi đó là vi phạm thuần khiết render).
  const firstHighlightIndex = useMemo(() => {
    if (!doc?.highlight) return -1;
    return blocks.findIndex((b) => blockOverlapsHighlight(b, doc.highlight!.start, doc.highlight!.end));
  }, [blocks, doc]);

  useEffect(() => {
    if (doc?.highlight) {
      firstHighlightRef.current?.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }, [doc, blocks]);

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

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH · Tài liệu chính sách</span>
        <h1 className="mono" style={{ fontSize: 20 }}>{doc.filename}</h1>
        <p className="sub">Toàn văn tài liệu — đoạn trích khớp câu tra cứu được tô sáng bên dưới, nếu có.</p>
      </div>

      <div className="card" style={{ lineHeight: 1.7 }}>
        {blocks.map((b, i) => {
          const trongVungToSang = doc.highlight != null && blockOverlapsHighlight(b, doc.highlight.start, doc.highlight.end);
          const laDiemCuonDau = i === firstHighlightIndex;

          const wrapperStyle: React.CSSProperties = trongVungToSang
            ? { background: "var(--warning-bg)", borderRadius: 6, padding: "2px 8px", margin: "0 -8px" }
            : {};

          if (b.type === "url") {
            return (
              <div key={i} ref={laDiemCuonDau ? firstHighlightRef : undefined} className="faint mono" style={{ fontSize: 12, marginBottom: 10, ...wrapperStyle }}>
                {b.text}
              </div>
            );
          }
          if (b.type === "heading") {
            return (
              <div
                key={i}
                ref={laDiemCuonDau ? firstHighlightRef : undefined}
                style={{ fontWeight: 700, fontSize: 15, marginTop: 18, marginBottom: 4, ...wrapperStyle }}
              >
                {b.text}
              </div>
            );
          }
          return (
            <p key={i} ref={laDiemCuonDau ? firstHighlightRef : undefined} style={{ marginBottom: 10, whiteSpace: "pre-wrap", ...wrapperStyle }}>
              {b.text}
            </p>
          );
        })}
      </div>
    </>
  );
}
