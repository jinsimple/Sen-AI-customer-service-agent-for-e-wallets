"use client";

import { useEffect, useState } from "react";
import { ApiError, getReportSummary } from "@/lib/api";
import { COMPLAINT_TYPE_LABEL, SCOPE_LABEL, type ComplaintType, type ReportSummary, type Scope } from "@/lib/types";

// KHÔNG dùng token thương hiệu (--navy/--gold) — thương hiệu là MỘT màu để
// đồng bộ, biểu đồ phân loại cần các màu TÁCH XA nhau để phân biệt. Đổi bộ
// màu thương hiệu (tím → lục → Stripe) từng làm 2/4 cột trùng màu vì cả hai
// đọc chung token. --chart-1..4 độc lập, chọn từ bảng colorblind-safe.
const BAR_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)"];

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
            {/* B3 (20/08) — mẫu số đi cạnh mọi %, đừng để người xem tự đoán */}
            <span className="mono">
              {pct}% <span className="dim">({count}/{total})</span>
            </span>
          </div>
        );
      })}
      {entries.length === 0 && <div className="dim" style={{ fontSize: 13 }}>Chưa có dữ liệu.</div>}
    </div>
  );
}

// B3 — mẫu số nhỏ dưới mỗi %, cùng khuôn cho mọi ô KPI phần trăm trong trang.
function MauSo({ n, d }: { n: number; d: number }) {
  return (
    <div className="kpi-trend mono" style={{ marginTop: 2 }}>
      ({n}/{d})
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
    void Promise.resolve().then(load);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Báo cáo vận hành</span>
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
              {/* B1 — nhãn cũ "Thời gian xử lý TB" hứa AHT nhưng đo CYCLE TIME
                  (tạo vé → sếp duyệt, GỒM CẢ thời gian nằm chờ). Đổi tên đúng
                  thứ đang đo, không đổi số. */}
              <div className="kpi-label">Thời gian từ tiếp nhận đến phê duyệt (cycle time)</div>
              <div className="kpi-value">
                {summary.avg_processing_hours != null ? `${summary.avg_processing_hours} giờ` : "—"}
              </div>
              {/* B3 — trung bình không có "mẫu số/tổng", chỉ có CỠ MẪU: bao
                  nhiêu case góp vào con số trung bình này. */}
              <div className="kpi-trend">tính trên {summary.avg_processing_hours_n} case đã duyệt</div>
            </div>
            <div className="card kpi">
              {/* B1 — AHT thật (thời gian NGƯỜI thao tác) chưa đo được: DB
                  không có mốc CSKH bắt đầu làm. Hiện rõ "chưa đo được", đừng
                  để trống — ô trống bị đọc thành 0. */}
              <div className="kpi-label">AHT — thời gian người thao tác thật</div>
              <div className="kpi-value dim">Chưa đo được</div>
              <div className="kpi-trend">{summary.aht_khong_do_duoc_ly_do}</div>
            </div>
            <div className="card kpi">
              {/* B2 — bảng resolutions luôn do CSKH tạo (propose_resolution
                  KHÔNG nằm trong 5 tool AI được gọi, contracts/agent-tools.yaml
                  — ràng buộc cứng 2). Nhãn cũ gán nhầm hành động này cho AI. */}
              <div className="kpi-label">% đề xuất của CSKH được sếp duyệt</div>
              <div className="kpi-value">
                {summary.pct_ai_proposal_approved != null ? `${summary.pct_ai_proposal_approved}%` : "—"}
              </div>
              <MauSo n={summary.pct_ai_proposal_approved_numerator} d={summary.pct_ai_proposal_approved_n} />
            </div>
            <div className="card kpi">
              <div className="kpi-label">% escalate</div>
              <div className="kpi-value">{summary.pct_escalated != null ? `${summary.pct_escalated}%` : "—"}</div>
              <MauSo n={summary.pct_escalated_numerator} d={summary.pct_escalated_n} />
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
