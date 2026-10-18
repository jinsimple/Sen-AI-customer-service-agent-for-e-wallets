"use client";

import { useState } from "react";
import { ApiError, approveResolution, rejectResolution, requestResolutionApprovalOtp } from "@/lib/api";
import { REJECT_REASON_LABEL, labelOf, type RejectReason } from "@/lib/types";
import { useI18n } from "@/lib/i18n/client";
import { rich } from "@/lib/i18n/rich";
import OtpInput from "@/components/OtpInput";

const REJECT_REASON_VALUES = Object.keys(REJECT_REASON_LABEL) as RejectReason[];

/**
 * The approve/reject button cluster for ONE proposal, with the OTP step.
 *
 * Split out for reuse (hotfix 2, Aug 14) because this cluster now appears in TWO places: the
 * `/approve` queue and the ticket detail screen. Copy-pasting two copies is the surest way for only
 * one copy to get patched one day — and this is the path to an action that touches money, the place
 * least allowed to drift apart.
 *
 * AUTH5-04: approving needs a SEPARATE OTP for the EXACT resolution_id being approved (PSD2 dynamic
 * linking, bound to the exact amount at the time the code was requested).
 *
 * P0 hotfix, Aug 31: patch `bdaf17e` stopped returning `otp_code` in the response body
 * (OTP_DEMO_MODE off by default) — the supervisor now has to TYPE the code received through another
 * channel themselves, sharing `OtpInput` with the customer flow (see `@/components/OtpInput.tsx`).
 *
 * This component does NOT check permissions itself: the caller must ensure it only renders for a
 * supervisor. Real enforcement still comes from the backend (require_role + OTP); the UI only
 * mirrors the authority-matrix correctly.
 */
export default function ResolutionApprovalActions({
  resolutionId,
  onDone,
  onError,
}: {
  resolutionId: string;
  onDone: () => void | Promise<void>;
  onError: (msg: string) => void;
}) {
  const { t, lang } = useI18n();
  const [busy, setBusy] = useState(false);
  // ADR-060 (Sep 3) — `otpCode` is only something other than `undefined` when the backend is
  // running OTP_DEMO_MODE (gated at the /request-approval-otp route, main.py:998, untouched here).
  // Production doesn't set that flag ⟹ this field is always undefined ⟹ the line showing the code
  // below doesn't render — mirroring exactly how ChatClient shows demoOtpCode for the login OTP, no
  // new mechanism invented.
  const [otp, setOtp] = useState<{ sessionId: string; otpCode?: string } | null>(null);
  const [otpError, setOtpError] = useState<string | null>(null);
  // ADR-019 — a rejection must carry a structured reason, so the "Reject" button now opens a
  // reason-picker form first instead of submitting directly as before.
  const [chonLyDo, setChonLyDo] = useState(false);
  const [reason, setReason] = useState("");

  async function handleRequestApprovalOtp() {
    setBusy(true);
    try {
      const res = await requestResolutionApprovalOtp(resolutionId);
      setOtp({ sessionId: res.session_id, otpCode: res.otp_code });
      setOtpError(null);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : t("approval.otpRequestFailed"));
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirmApprove(otpCode: string) {
    if (!otp) return;
    setBusy(true);
    setOtpError(null);
    try {
      await approveResolution(resolutionId, otp.sessionId, otpCode);
      setOtp(null);
      await onDone();
    } catch (e) {
      const msg = e instanceof ApiError ? e.message : t("approval.approveFailed");
      setOtpError(msg);
      onError(msg);
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    if (!reason) return;
    setBusy(true);
    try {
      await rejectResolution(resolutionId, reason as RejectReason);
      setChonLyDo(false);
      setReason("");
      await onDone();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : t("approval.rejectFailed"));
    } finally {
      setBusy(false);
    }
  }

  if (otp) {
    return (
      <div className="note callout-gold approval-otp-row" style={{ marginTop: 16 }}>
        <div>
          {t("approval.enterOtp")}
        </div>
        {otp.otpCode && (
          <div className="otp-meta">
            {t("approval.demoOtp")} <strong>{otp.otpCode}</strong>
          </div>
        )}
        <OtpInput
          disabled={false}
          checking={busy}
          error={otpError}
          onSubmit={(otpCode) => void handleConfirmApprove(otpCode)}
          trailing={
            <button className="btn btn-outline btn-sm" disabled={busy} onClick={() => setOtp(null)}>
              {t("common.cancel")}
            </button>
          }
        />
      </div>
    );
  }

  if (chonLyDo) {
    return (
      <div className="note" style={{ marginTop: 16 }}>
        <div className="field" style={{ marginTop: 0 }}>
          <label>{t("approval.rejectReason")}</label>
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="">{t("approval.chooseReason")}</option>
            {REJECT_REASON_VALUES.map((value) => (
              <option key={value} value={value}>{labelOf(REJECT_REASON_LABEL, value, lang)}</option>
            ))}
          </select>
        </div>
        {/* Ranh giới ghi trong contract v2.1.0: thiếu-tạm-thời thì trả case về
            cho CSKH bổ sung, đừng từ chối hẳn — nếu không ta mất khả năng phân
            biệt "sửa được" với "sai hẳn" trong chính dữ liệu dùng để học. */}
        {reason === "thieu_can_cu" && (
          <div className="dim" style={{ fontSize: 12, marginTop: 8 }}>
            {rich(t("approval.insufficientHint"))}
          </div>
        )}
        <div className="flex gap-sm wrap" style={{ marginTop: 12 }}>
          <button className="btn btn-danger-outline" disabled={busy || !reason} onClick={handleReject}>
            {t("approval.confirmReject")}
          </button>
          <button className="btn btn-outline" disabled={busy} onClick={() => { setChonLyDo(false); setReason(""); }}>
            {t("common.cancel")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-sm wrap" style={{ marginTop: 16 }}>
      <button className="btn btn-success" disabled={busy} onClick={handleRequestApprovalOtp}>
        <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg>
        {t("approval.approve")}
      </button>
      <button className="btn btn-danger-outline" disabled={busy} onClick={() => setChonLyDo(true)}>
        <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" /></svg>
        {t("approval.reject")}
      </button>
    </div>
  );
}
