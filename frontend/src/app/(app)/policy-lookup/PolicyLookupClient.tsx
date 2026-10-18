"use client";

import { useState } from "react";
import { ApiError, searchPolicy } from "@/lib/api";
import type { PolicySearchResultItem } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";

export default function PolicyLookupClient() {
  const { t } = useI18n();
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
      setError(e instanceof ApiError ? e.message : t("policyLookup.failed"));
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <span className="eyebrow">{t("policyLookup.eyebrow")}</span>
        <h1>{t("policyLookup.title")}</h1>
        <p className="sub">
          {t("policyLookup.sub")}
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSearch} className="flex gap-sm wrap center-y">
          <input
            style={{ flex: 1, minWidth: 260 }}
            placeholder={t("policyLookup.placeholder")}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button className="btn btn-gold" type="submit" disabled={loading}>
            {loading ? t("policyLookup.searching") : t("policyLookup.search")}
          </button>
        </form>
      </div>

      {error && <div className="note" style={{ borderColor: "var(--danger)", marginTop: 18 }}>{error}</div>}

      {searched && !error && (
        <div className="section" style={{ marginTop: 24 }}>
          {results?.length === 0 ? (
            <div className="dim">{t("policyLookup.none")}</div>
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
                      {t("policyLookup.fullText")}
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
