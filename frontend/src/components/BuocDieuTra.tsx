"use client";

import { useState } from "react";
import { formatDateTime } from "@/lib/format";
import { traiPayload, type DongHienThi } from "@/lib/timeline-format";
import { TOOL_NAME_LABEL, labelOf } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

// UI-01 — MỘT bước trong "Nhật ký điều tra", hiển thị cho NGƯỜI đọc.
//
// DÙNG CHUNG cho cskh và supervisor — CÓ CHỦ ĐÍCH. Sếp duyệt dựa trên đúng
// thứ CSKH nhìn thấy; hai vai nhìn hai bản khác nhau là mầm của "tôi thấy
// khác cơ" giữa lúc tranh luận một quyết định hoàn tiền.
//
// KHÔNG có nút sao chép / xuất — cho cả `agent_note` lẫn expander JSON.
// `agent_note` chưa qua scrub, chưa có trần độ dài, chưa có cờ (S-02, chờ B3);
// một trường tự do chưa che cộng với một nút copy là bề mặt TRÍCH XUẤT HÀNG
// LOẠT. Người cần đối chiếu vẫn bôi đen chép tay được — chậm hơn đúng mức.

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

// Kết quả tra cứu lịch sử khách có thể ra HÀNG TRĂM dòng (đo thật trên dữ
// liệu demo: một bước `get_customer_history` trải ra 144 dòng). Đổ hết ra màn
// hình là phá đúng tiêu chí nghiệm thu "CSKH đọc một bước là hiểu".
//
// Cắt hiển thị, KHÔNG cắt dữ liệu: phần còn lại mở ra bằng một cú bấm, và bản
// đầy đủ vẫn nằm nguyên trong expander "dữ liệu kỹ thuật". Không tóm tắt,
// không chọn lọc "dòng quan trọng" — chọn hộ là lớp DIỄN GIẢI, thứ ràng buộc
// cứng 3 cấm ở đây.
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

  // Ba ca `null` GỘP LÀM MỘT nhãn ở v1 (không có bản ghi · tool timeout · tra
  // được nhưng rỗng) — chấp nhận có ý thức, ghi ở đây để không ai đọc timeline
  // rồi kết luận "hệ thống không có dữ liệu" khi thật ra lượt tra đã hỏng.
  // `ly_do_fallback` tách được nếu về sau cần.
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
