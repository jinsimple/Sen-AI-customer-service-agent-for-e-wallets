"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { ApiError, getPolicyDoc } from "@/lib/api";
import type { PolicyDocFullText } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import { blockOverlapsHighlight, splitPolicyDocBlocks } from "@/lib/policyDocBlocks";

// ADR-065 (Sep 5) — the "View full text" deep-link from /policy-lookup, opened in a NEW TAB.
// Auto-scrolls to and highlights the matched excerpt when a `chunk_id` is present — a one-paragraph
// document (short FAQ) just shows its full text with nothing to scroll to (the highlighted span is
// nearly the whole page; scrollIntoView still runs correctly, there's just nowhere further to
// scroll).
//
// [polish Sep 5, caught by the PO from a screenshot] `full_text` is read raw from the docx: a
// SECTION/ARTICLE heading sticks to the end of the previous sentence (no line break), and dumping
// it straight into one `pre-wrap` block turns the whole page into a single flat paragraph.
// `splitPolicyDocBlocks` (lib/policyDocBlocks.ts) splits it into heading/url/paragraph blocks —
// highlighting switched from a CHARACTER-RANGE match to a BLOCK overlapping [highlight.start, end)
// (which also fixes the sticking, since the stuck heading is now its own block).
export default function PolicyDocPage() {
  const { t } = useI18n();
  const { docId } = useParams<{ docId: string }>();
  const searchParams = useSearchParams();
  const chunkId = searchParams.get("chunk_id") ?? undefined;

  const [doc, setDoc] = useState<PolicyDocFullText | null>(null);
  const [error, setError] = useState<string | null>(null);
  const firstHighlightRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    getPolicyDoc(docId, chunkId)
      .then(setDoc)
      .catch((e) => setError(e instanceof ApiError ? e.message : t("policyDoc.loadError")));
  }, [docId, chunkId, t]);

  const blocks = useMemo(() => {
    if (!doc?.full_text) return [];
    return splitPolicyDocBlocks(doc.full_text).filter((b) => b.type !== "blank");
  }, [doc]);

  // ADR-065 (Sep 5) — the "View full text" deep-link from /policy-lookup, opened in a NEW TAB.
  // Auto-scrolls to and highlights the matched excerpt when a `chunk_id` is present — a
  // one-paragraph document (short FAQ) just shows its full text with nothing to scroll to (the
  // highlighted span is nearly the whole page; scrollIntoView still runs correctly, there's just
  // nowhere further to scroll).
  //
  // [polish Sep 5, caught by the PO from a screenshot] `full_text` is read raw from the docx: a
  // SECTION/ARTICLE heading sticks to the end of the previous sentence (no line break), and dumping
  // it straight into one `pre-wrap` block turns the whole page into a single flat paragraph.
  // `splitPolicyDocBlocks` (lib/policyDocBlocks.ts) splits it into heading/url/paragraph blocks —
  // highlighting switched from a CHARACTER-RANGE match to a BLOCK overlapping [highlight.start,
  // end) (which also fixes the sticking, since the stuck heading is now its own block).
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
        <h1>{t("policyDoc.cantOpen")}</h1>
        <p className="sub">{error}</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="page-head">
        <p className="sub">{t("common.loading")}</p>
      </div>
    );
  }

  if (doc.full_text === null) {
    return (
      <div className="page-head">
        <span className="eyebrow">{t("policyDoc.eyebrow")}</span>
        <h1>{doc.filename}</h1>
        <p className="sub">
          {t("policyDoc.noFullText")}
        </p>
      </div>
    );
  }

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("policyDoc.eyebrow")}</span>
        <h1 className="mono" style={{ fontSize: 20 }}>{doc.filename}</h1>
        <p className="sub">{t("policyDoc.sub")}</p>
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
