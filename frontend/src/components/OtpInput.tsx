"use client";

import { useRef, useState } from "react";

/**
 * Ô nhập mã OTP 6 số dùng chung — tách ra từ `ChatClient.tsx` (luồng khách,
 * đợt vá `bdaf17e` 31/08) để dùng lại được ở `ResolutionApprovalActions.tsx`
 * (luồng sếp duyệt). Component KHÔNG tự biết mã OTP là gì — chỉ thu thập 6
 * số người dùng gõ rồi gọi `onSubmit`, đúng mô hình "khách/sếp tự nhận mã
 * qua kênh khác (SMS/CSDL), gõ tay vào đây" — không có đường nào tự điền sẵn.
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
  // [05/09, PO chốt] Tuỳ chọn — nút PHỤ đặt CÙNG HÀNG với "Xác nhận" (vd
  // "Huỷ" ở luồng Sếp duyệt, ResolutionApprovalActions.tsx). KHÔNG truyền
  // (mặc định, luồng khách ChatClient.tsx) ⟹ render nút Xác nhận Y HỆT
  // trước khi có prop này — luồng khách byte-identical, rủi ro = 0.
  trailing?: React.ReactNode;
}) {
  // Controlled (không thao tác DOM tay) — bắt buộc để gõ ĐÈ lên ô đã có sẵn
  // số hoạt động đúng: input maxLength=1 chưa được bôi đen thì trình duyệt
  // chặn ký tự mới (đã đạt maxLength), onChange không bắn, không tự nhảy ô.
  // onFocus bôi đen nội dung cũ để gõ đè luôn thay thế được, dù gõ theo thứ
  // tự nào hay quay lại ô đã điền.
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
          Nhập đủ 6 số OTP để tiếp tục.
        </div>
      )}
      {trailing ? (
        <div className="flex gap-sm wrap" style={{ marginTop: 12 }}>
          <button
            className="btn btn-gold btn-sm"
            disabled={!canSubmit}
            onClick={() => onSubmit(digits.join(""))}
          >
            {checking ? "Đang xác thực..." : "Xác nhận"}
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
          {checking ? "Đang xác thực..." : "Xác nhận"}
        </button>
      )}
    </>
  );
}
