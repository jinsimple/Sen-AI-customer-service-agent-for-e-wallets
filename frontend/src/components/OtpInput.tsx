"use client";

import { useRef, useState } from "react";
import { useI18n } from "@/lib/i18n/client";

/**
 * A shared 6-digit OTP input — split out of `ChatClient.tsx` (customer flow, patch `bdaf17e`, Aug
 * 31) to be reused in `ResolutionApprovalActions.tsx` (supervisor-approval flow). The component
 * doesn't itself know what the OTP is — it only collects the 6 digits the user types and calls
 * `onSubmit`, matching the model "customer/supervisor receives the code through another channel
 * (SMS/DB), types it in here" — there is no path that pre-fills it.
 */
export default function OtpInput({
  disabled,
  checking,
  error,
  onSubmit,
  trailing,
}: {
  disabled: boolean;
  checking: boolean;
  error: string | null;
  onSubmit: (otpCode: string) => void;
  // [Sep 5, PO decision] Optional — a SECONDARY button placed on the SAME ROW as "Confirm" (e.g.
  // "Cancel" in the supervisor-approval flow, ResolutionApprovalActions.tsx). NOT passed (the
  // default, the customer flow in ChatClient.tsx) ⟹ renders the Confirm button EXACTLY as before
  // this prop existed — the customer flow is byte-identical, zero risk.
  trailing?: React.ReactNode;
}) {
  // Controlled (no manual DOM manipulation) — required so typing OVER an already-filled digit works
  // correctly: an input with maxLength=1 that isn't selected blocks a new character (maxLength
  // already reached), onChange never fires, and it never auto-advances to the next box. onFocus
  // selects the existing content so typing always overwrites it, regardless of typing order or
  // jumping back to an already-filled box.
  const { t } = useI18n();
  const [digits, setDigits] = useState(["", "", "", "", "", ""]);
  const refs = useRef<Array<HTMLInputElement | null>>([]);

  function handleChange(i: number, value: string) {
    const digit = value.replace(/\D/g, "").slice(-1);
    setDigits((prev) => {
      const next = [...prev];
      next[i] = digit;
      return next;
    });
    if (digit && i < 5) refs.current[i + 1]?.focus();
  }

  function handleKeyDown(i: number, e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Backspace" && !digits[i] && i > 0) {
      refs.current[i - 1]?.focus();
    }
    if (e.key === "Enter" && canSubmit) onSubmit(digits.join(""));
  }

  const canSubmit = !disabled && !checking && digits.every(Boolean);

  return (
    <>
      <div className="otp-row">
        {digits.map((d, i) => (
          <input
            key={i}
            ref={(el) => {
              refs.current[i] = el;
            }}
            className="otp-box"
            inputMode="numeric"
            maxLength={1}
            value={d}
            disabled={disabled || checking}
            onChange={(e) => handleChange(i, e.target.value)}
            onKeyDown={(e) => handleKeyDown(i, e)}
            onFocus={(e) => e.target.select()}
          />
        ))}
      </div>
      {error && (
        <div className="dim" style={{ color: "var(--danger, #d33)", fontSize: 12, marginTop: 6 }}>
          {error}
        </div>
      )}
      {!error && !canSubmit && !checking && digits.some(Boolean) && (
        <div className="dim" style={{ fontSize: 12, marginTop: 6 }}>
          {t("otp.needSix")}
        </div>
      )}
      {trailing ? (
        <div className="flex gap-sm wrap" style={{ marginTop: 12 }}>
          <button
            className="btn btn-gold btn-sm"
            disabled={!canSubmit}
            onClick={() => onSubmit(digits.join(""))}
          >
            {checking ? t("common.verifying") : t("common.confirm")}
          </button>
          {trailing}
        </div>
      ) : (
        <button
          className="btn btn-gold btn-sm"
          style={{ marginTop: 12 }}
          disabled={!canSubmit}
          onClick={() => onSubmit(digits.join(""))}
        >
          {checking ? t("common.verifying") : t("common.confirm")}
        </button>
      )}
    </>
  );
}
