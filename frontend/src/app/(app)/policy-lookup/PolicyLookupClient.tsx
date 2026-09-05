"use client";

import { useState } from "react";
import { ApiError, searchPolicy } from "@/lib/api";
import type { PolicySearchResultItem } from "@/lib/types";

export default function PolicyLookupClient() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PolicySearchResultItem[] | null>(null);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await searchPolicy(query.trim());
      setResults(res.results);
      setSearched(true);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Tra cứu thất bại");
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">Webapp CSKH · Tra cứu chính sách</span>
        <h1>Tra cứu chính sách & FAQ</h1>
        <p className="sub">
          Tìm nhanh nội dung chính sách/FAQ mới nhất do đối tác ví cập nhật — hữu ích khi xử lý ticket
          cần đối chiếu quy định. Kết quả là đoạn trích nguyên văn, không qua tổng hợp AI.
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-sm wrap center-y">
          <input
            style={{ flex: 1, minWidth: 260 }}
            placeholder="Vd: phí rút tiền, thời gian hoàn tiền double_charge..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-gold" type="submit" disabled={loading}>
            {loading ? "Đang tìm…" : "Tìm kiếm"}
          </button>
        </form>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)", marginTop: 18 }}>{error}</div>}

      {searched && !error && (
        <div className="section" style={{ marginTop: 24 }}>
          {results?.length === 0 ? (
            <div className="dim">Chưa tìm thấy tài liệu chính sách nào khớp với câu hỏi này.</div>
          ) : (
            <div className="flex-col gap-md">
              {results?.map((r, i) => (
                <div className="card" key={`${r.doc_id}-${i}`}>
                  <div className="flex between center-y">
                    <div className="card-title mono" style={{ fontSize: 13 }}>{r.source_filename}</div>
                    {/* ADR-065 (05/09) — mở TAB MỚI, tự cuộn+tô sáng đúng đoạn này. */}
                    <a
                      className="mono"
                      style={{ fontSize: 12, fontWeight: 600 }}
                      href={`/policy-doc/${r.doc_id}?chunk_id=${encodeURIComponent(r.chunk_id)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Xem toàn văn ↗
                    </a>
                  </div>
                  <p style={{ marginTop: 8, whiteSpace: "pre-wrap" }}>{r.text}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </>
  );
}
