"use client";

import { useState } from "react";
import { formatDateTime } from "@/lib/format";
import { traiPayload, type DongHienThi } from "@/lib/timeline-format";
import { TOOL_NAME_LABEL, labelOf } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

// UI-01 — ONE step in the "investigation log", shown to a HUMAN reader.
//
// SHARED between support agent and supervisor — DELIBERATELY. The supervisor approves based on
// exactly what the support agent saw; two roles seeing two different versions is the seed of "I saw
// something different" in the middle of a refund-decision argument.
//
// NO copy / export button — for either `agent_note` or the JSON expander. `agent_note` is not
// scrubbed, has no length cap, no flag yet (S-02, pending B3); a free-text field that's not masked
// plus a copy button is a BULK-EXFILTRATION surface. Anyone who needs to copy it can still select
// and copy by hand — slower, as it should be.

type Log = {
  step_no: number;
  tool_called: string;
  tool_input: unknown;
  tool_result: unknown;
  tool_result_id: string | null;
  agent_note?: string | null;
  created_at: string;
};

function Dong({ d }: { d: DongHienThi }) {
  return (
    <div style={{ display: "flex", gap: 8, paddingLeft: d.sau * 14, lineHeight: 1.7 }}>
      {d.nhan && (
        <span className="dim" style={{ minWidth: 148, flexShrink: 0, fontSize: 12 }}>
          {d.nhan}
        </span>
      )}
      <span style={{ fontSize: 13, wordBreak: "break-word" }}>{d.giaTri}</span>
    </div>
  );
}

function Khoi({ tieuDe, payload }: { tieuDe: string; payload: unknown }) {
  const { lang } = useI18n();
  return (
    <div style={{ marginTop: 8 }}>
      <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{tieuDe}</div>
      {traiPayload(payload, 0, "", lang).map((d, i) => (
        <Dong key={i} d={d} />
      ))}
    </div>
  );
}

// A customer-history lookup can produce HUNDREDS of rows (measured on demo data: one
// `get_customer_history` step spans 144 rows). Dumping it all onto the screen breaks the exact
// acceptance criterion "a support agent reads one step and understands it".
//
// Cut the DISPLAY, not the DATA: the rest opens with one click, and the full version still sits
// intact inside the "technical data" expander. No summarising, no picking "the important rows" —
// picking for the reader is the INTERPRETATION layer, which hard constraint 3 forbids here.
const NGUONG_DONG = 12;

function KetQuaDai({ dong }: { dong: DongHienThi[] }) {
  const { t } = useI18n();
  const [moHet, setMoHet] = useState(false);
  const hien = moHet ? dong : dong.slice(0, NGUONG_DONG);
  const con = dong.length - hien.length;
  return (
    <>
      {hien.map((d, i) => (
        <Dong key={i} d={d} />
      ))}
      {con > 0 && (
        <button
          type="button"
          onClick={() => setMoHet(true)}
          className="dim"
          style={{ fontSize: 11, marginTop: 4, background: "none", border: "none", padding: 0, cursor: "pointer", textDecoration: "underline" }}
        >
          {t("step.showMore", { n: con })}
        </button>
      )}
      {moHet && dong.length > NGUONG_DONG && (
        <button
          type="button"
          onClick={() => setMoHet(false)}
          className="dim"
          style={{ fontSize: 11, marginTop: 4, background: "none", border: "none", padding: 0, cursor: "pointer", textDecoration: "underline" }}
        >
          {t("step.collapse")}
        </button>
      )}
    </>
  );
}

export default function BuocDieuTra({ log }: { log: Log }) {
  const { t, lang } = useI18n();
  const [moKyThuat, setMoKyThuat] = useState(false);

  // Three `null` cases LUMPED INTO one label in v1 (no record logged · tool timeout · looked up but
  // empty) — a conscious trade-off, noted here so no one reads the timeline and concludes "the
  // system has no data" when actually the lookup itself failed. `ly_do_fallback` (fallback reason)
  // can be split out later if needed.
  const ketQuaTrong = log.tool_result === null || log.tool_result === undefined;
  const biChanOtp = ketQuaTrong && log.tool_result_id === null;

  return (
    <div className="trail-step" key={log.step_no}>
      <span className="trail-tool">
        {labelOf(TOOL_NAME_LABEL, log.tool_called, lang) ?? log.tool_called}
        {/* Tên kỹ thuật giữ lại dạng chữ nhỏ: đây là màn nội bộ, người điều
            tra vẫn cần đối chiếu tên tool thật khi đọc log backend. */}
        <span className="dim" style={{ fontSize: 11, marginLeft: 6, fontWeight: 400 }}>
          {log.tool_called}()
        </span>
      </span>

      <Khoi tieuDe={t("step.asked")} payload={log.tool_input} />

      <div style={{ marginTop: 8 }}>
        <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 2 }}>{t("step.result")}</div>
        {biChanOtp ? (
          <div className="dim" style={{ fontSize: 13, fontStyle: "italic" }}>
            {t("step.blockedOtp")}
          </div>
        ) : ketQuaTrong ? (
          <div className="dim" style={{ fontSize: 13, fontStyle: "italic" }}>
            {t("step.noData")}
          </div>
        ) : (
          <KetQuaDai dong={traiPayload(log.tool_result, 0, "", lang)} />
        )}
      </div>

      {log.agent_note && <div className="trail-note">{log.agent_note}</div>}

      {/* Dữ liệu gốc GIỮ NGUYÊN VĂN và luôn truy được — đây là bằng chứng đối
          chiếu chống bịa số liệu (ràng buộc cứng 3). Lớp nhãn tiếng Việt bên
          trên là tiện ích đọc, KHÔNG thay thế nó. Mặc định ĐÓNG. */}
      <details open={moKyThuat} onToggle={(e) => setMoKyThuat((e.target as HTMLDetailsElement).open)}>
        <summary className="dim" style={{ fontSize: 11, cursor: "pointer", marginTop: 6 }}>
          {t("step.technical")}
        </summary>
        <pre
          style={{
            fontSize: 11,
            whiteSpace: "pre-wrap",
            wordBreak: "break-all",
            marginTop: 4,
            opacity: 0.75,
          }}
        >
          {JSON.stringify({ input: log.tool_input, result: log.tool_result }, null, 2)}
        </pre>
      </details>

      <div className="trail-time">{formatDateTime(log.created_at, lang)}</div>
    </div>
  );
}
