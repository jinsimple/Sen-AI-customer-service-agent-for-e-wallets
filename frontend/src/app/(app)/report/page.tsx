"use client";

import { useEffect, useState } from "react";
import { ApiError, getReportSummary } from "@/lib/api";
import {
  COMPLAINT_TYPE_LABEL,
  COMPLAINT_TYPE_LABEL_EN,
  SCOPE_LABEL,
  SCOPE_LABEL_EN,
  type ComplaintType,
  type ReportSummary,
  type Scope,
} from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

// Deliberately NOT using brand tokens (--navy/--gold) — the brand is ONE colour for consistency,
// while a categorical chart needs colours that are FAR APART to tell apart. Switching the brand
// palette (purple → green → Stripe) once made 2 of 4 columns the same colour because both read the
// same token. --chart-1..4 are independent, picked from a colorblind-safe palette.
const BAR_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];

function BarList({ data, labels }: { data: Record<string, number>; labels: Record<string, string> }) {
  const { t } = useI18n();
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  return (
    <div className="barchart">
      {entries.map(([key, count], i) => {
        const pct = Math.round((count / total) * 100);
        return (
          <div className="barrow" key={key}>
            <span>{labels[key] ?? key}</span>
            <div className="bartrack">
              <div className="barfill" style={{ width: `${pct}%`, background: BAR_COLORS[i % BAR_COLORS.length] }} />
            </div>
            {/* B3 (20/08) — mẫu số đi cạnh mọi %, đừng để người xem tự đoán */}
            <span className="mono">
              {pct}% <span className="dim">({count}/{total})</span>
            </span>
          </div>
        );
      })}
      {entries.length === 0 && <div className="dim" style={{ fontSize: 13 }}>{t("report.noData")}</div>}
    </div>
  );
}

// B3 — a small denominator under every %, the same pattern for every percentage KPI tile on the
// page.
function MauSo({ n, d }: { n: number; d: number }) {
  return (
    <div className="kpi-trend mono" style={{ marginTop: 2 }}>
      ({n}/{d})
    </div>
  );
}

export default function ReportPage() {
  const { t, lang } = useI18n();
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  async function load() {
    setError(null);
    try {
      const s = await getReportSummary({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setSummary(s);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : t("report.loadError"));
    }
  }

  useEffect(() => {
    void Promise.resolve().then(load);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("report.title")}</span>
        <h1>{t("report.title")}</h1>
        <p className="sub">{t("report.sub")}</p>
      </div>

      <div className="flex gap-sm center-y" style={{ marginBottom: 20 }}>
        <input
          type="date"
          value={dateFrom}
          onChange={(e) => setDateFrom(e.target.value)}
          style={{ padding: "8px 12px", border: "1.5px solid var(--border)", borderRadius: 9, background: "var(--surface)", color: "var(--text)" }}
        />
        <span className="dim">–</span>
        <input
          type="date"
          value={dateTo}
          onChange={(e) => setDateTo(e.target.value)}
          style={{ padding: "8px 12px", border: "1.5px solid var(--border)", borderRadius: 9, background: "var(--surface)", color: "var(--text)" }}
        />
        <button className="btn btn-outline btn-sm" onClick={load}>{t("report.apply")}</button>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      {summary && (
        <>
          <div className="kpi-grid" style={{ marginBottom: 26 }}>
            <div className="card kpi">
              {/* B1 — nhãn cũ "Thời gian xử lý TB" hứa AHT nhưng đo CYCLE TIME
                  (tạo vé → sếp duyệt, GỒM CẢ thời gian nằm chờ). Đổi tên đúng
                  thứ đang đo, không đổi số. */}
              <div className="kpi-label">{t("report.cycleTime")}</div>
              <div className="kpi-value">
                {summary.avg_processing_hours != null ? t("report.hours", { n: summary.avg_processing_hours }) : "—"}
              </div>
              {/* B3 — trung bình không có "mẫu số/tổng", chỉ có CỠ MẪU: bao
                  nhiêu case góp vào con số trung bình này. */}
              <div className="kpi-trend">{t("report.basedOn", { n: summary.avg_processing_hours_n })}</div>
            </div>
            <div className="card kpi">
              {/* B1 — AHT thật (thời gian NGƯỜI thao tác) chưa đo được: DB
                  không có mốc CSKH bắt đầu làm. Hiện rõ "chưa đo được", đừng
                  để trống — ô trống bị đọc thành 0. */}
              <div className="kpi-label">{t("report.aht")}</div>
              <div className="kpi-value dim">{t("report.notMeasured")}</div>
              <div className="kpi-trend">{summary.aht_khong_do_duoc_ly_do}</div>
            </div>
            <div className="card kpi">
              {/* B2 — bảng resolutions luôn do CSKH tạo (propose_resolution
                  KHÔNG nằm trong 5 tool AI được gọi, contracts/agent-tools.yaml
                  — ràng buộc cứng 2). Nhãn cũ gán nhầm hành động này cho AI. */}
              <div className="kpi-label">{t("report.pctApproved")}</div>
              <div className="kpi-value">
                {summary.pct_ai_proposal_approved != null ? `${summary.pct_ai_proposal_approved}%` : "—"}
              </div>
              <MauSo n={summary.pct_ai_proposal_approved_numerator} d={summary.pct_ai_proposal_approved_n} />
            </div>
            <div className="card kpi">
              <div className="kpi-label">{t("report.pctEscalated")}</div>
              <div className="kpi-value">{summary.pct_escalated != null ? `${summary.pct_escalated}%` : "—"}</div>
              <MauSo n={summary.pct_escalated_numerator} d={summary.pct_escalated_n} />
            </div>
            <div className="card kpi">
              <div className="kpi-label">{t("report.total")}</div>
              <div className="kpi-value">{summary.total_tickets}</div>
            </div>
          </div>

          <div className="grid grid-2">
            <div className="card">
              <div className="card-title">{t("report.byType")}</div>
              <BarList data={summary.by_complaint_type} labels={(lang === "en" ? COMPLAINT_TYPE_LABEL_EN : COMPLAINT_TYPE_LABEL) as Record<ComplaintType, string>} />
            </div>
            <div className="card">
              <div className="card-title">{t("report.byScope")}</div>
              <BarList data={summary.by_scope} labels={(lang === "en" ? SCOPE_LABEL_EN : SCOPE_LABEL) as Record<Scope, string>} />
            </div>
          </div>
        </>
      )}
    </>
  );
}
