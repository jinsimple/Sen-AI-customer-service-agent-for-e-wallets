"use client";

import { useEffect, useState } from "react";
import { ApiError, getReportSummary } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, SCOPE_LABEL, type ComplaintType, type ReportSummary, type Scope } from "@/lib/types";

const BAR_COLORS = ["var(--navy)", "var(--navy-2)", "var(--gold)", "var(--warning)"];

function BarList({ data, labels }: { data: Record<string, number>; labels: Record<string, string> }) {
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
            <span className="mono">{pct}%</span>
          </div>
        );
      })}
      {entries.length === 0 && <div className="dim" style={{ fontSize: 13 }}>Chưa có dữ liệu.</div>}
    </div>
  );
}

export default function ReportPage() {
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
      setError(e instanceof ApiError ? e.message : "Không tải được báo cáo");
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp Sếp · US-018</span>
        <h1>Báo cáo vận hành</h1>
        <p className="sub">Số liệu tính trực tiếp từ dữ liệu ticket thật tại thời điểm xem — không phải ước lượng.</p>
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
        <button className="btn btn-outline btn-sm" onClick={load}>Áp dụng</button>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)" }}>{error}</div>}

      {summary && (
        <>
          <div className="kpi-grid" style={{ marginBottom: 26 }}>
            <div className="card kpi">
              <div className="kpi-label">Thời gian xử lý TB</div>
              <div className="kpi-value">
                {summary.avg_processing_hours != null ? `${summary.avg_processing_hours} giờ` : "—"}
              </div>
              <div className="kpi-trend">tính trên case đã duyệt</div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">% đề xuất AI được duyệt</div>
              <div className="kpi-value">
                {summary.pct_ai_proposal_approved != null ? `${summary.pct_ai_proposal_approved}%` : "—"}
              </div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">% escalate</div>
              <div className="kpi-value">{summary.pct_escalated != null ? `${summary.pct_escalated}%` : "—"}</div>
            </div>
            <div className="card kpi">
              <div className="kpi-label">Tổng ticket trong kỳ</div>
              <div className="kpi-value">{summary.total_tickets}</div>
            </div>
          </div>

          <div className="grid grid-2">
            <div className="card">
              <div className="card-title">Phân bố theo loại khiếu nại</div>
              <BarList data={summary.by_complaint_type} labels={COMPLAINT_TYPE_LABEL as Record<ComplaintType, string>} />
            </div>
            <div className="card">
              <div className="card-title">Phân bố theo phạm vi giao dịch</div>
              <BarList data={summary.by_scope} labels={SCOPE_LABEL as Record<Scope, string>} />
            </div>
          </div>
        </>
      )}
    </>
  );
}
