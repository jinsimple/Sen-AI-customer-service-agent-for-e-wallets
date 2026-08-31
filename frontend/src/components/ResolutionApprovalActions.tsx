"use client";

import { useState } from "react";
import { ApiError, approveResolution, rejectResolution, requestResolutionApprovalOtp } from "@/lib/api";
import { REJECT_REASON_LABEL, type RejectReason } from "@/lib/types";
import OtpInput from "@/components/OtpInput";

const REJECT_REASONS = (Object.keys(REJECT_REASON_LABEL) as RejectReason[]).map((value) => ({
  value,
  label: REJECT_REASON_LABEL[value],
}));

/**
 * Cụm nút duyệt/từ chối MỘT đề xuất, kèm bước xin OTP.
 *
 * Tách ra dùng chung (hotfix 2, 14/08) vì cụm này giờ xuất hiện ở HAI nơi:
 * hàng chờ `/approve` và chi tiết ticket. Copy-paste hai bản là cách chắc
 * chắn nhất để một ngày nào đó chỉ một bản được vá — mà đây là đường đi tới
 * hành động chạm tiền, chỗ ít được phép lệch nhau nhất.
 *
 * AUTH5-04: duyệt cần OTP RIÊNG cho ĐÚNG resolution_id đang duyệt (PSD2
 * dynamic linking, gắn với đúng số tiền tại thời điểm xin mã).
 *
 * Hotfix P0 31/08: đợt vá `bdaf17e` ngừng trả `otp_code` qua response body
 * (OTP_DEMO_MODE mặc định tắt) — sếp giờ phải TỰ gõ mã nhận qua kênh khác,
 * dùng chung `OtpInput` với luồng khách (xem `@/components/OtpInput.tsx`).
 *
 * Component này KHÔNG tự kiểm quyền: nơi gọi phải tự bảo đảm chỉ render cho
 * supervisor. Quyền thật vẫn do backend ép (require_role + OTP), UI chỉ phản
 * chiếu cho đúng authority-matrix.
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
  const [busy, setBusy] = useState(false);
  const [otp, setOtp] = useState<{ sessionId: string } | null>(null);
  const [otpError, setOtpError] = useState<string | null>(null);
  // ADR-019 — từ chối phải kèm lý do có cấu trúc, nên nút "Từ chối" mở form
  // chọn lý do trước, không gửi thẳng như trước.
  const [chonLyDo, setChonLyDo] = useState(false);
  const [reason, setReason] = useState("");

  async function handleRequestApprovalOtp() {
    setBusy(true);
    try {
      const res = await requestResolutionApprovalOtp(resolutionId);
      setOtp({ sessionId: res.session_id });
      setOtpError(null);
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Không xin được mã OTP duyệt");
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
      const msg = e instanceof ApiError ? e.message : "Duyệt thất bại";
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
      onError(e instanceof ApiError ? e.message : "Từ chối thất bại");
    } finally {
      setBusy(false);
    }
  }

  if (otp) {
    return (
      <div className="note callout-gold approval-otp-row" style={{ marginTop: 16 }}>
        <div>
          Nhập mã OTP xác nhận duyệt (còn hiệu lực 10 phút, chỉ dùng được cho đúng đề xuất này):
        </div>
        <OtpInput
          disabled={false}
          checking={busy}
          error={otpError}
          onSubmit={(otpCode) => void handleConfirmApprove(otpCode)}
        />
        <div className="flex gap-sm wrap" style={{ marginTop: 8 }}>
          <button className="btn btn-outline" disabled={busy} onClick={() => setOtp(null)}>
            Huỷ
          </button>
        </div>
      </div>
    );
  }

  if (chonLyDo) {
    return (
      <div className="note" style={{ marginTop: 16 }}>
        <div className="field" style={{ marginTop: 0 }}>
          <label>Lý do từ chối</label>
          <select value={reason} onChange={(e) => setReason(e.target.value)}>
            <option value="">— chọn lý do —</option>
            {REJECT_REASONS.map((r) => (
              <option key={r.value} value={r.value}>{r.label}</option>
            ))}
          </select>
        </div>
        {/* Ranh giới ghi trong contract v2.1.0: thiếu-tạm-thời thì trả case về
            cho CSKH bổ sung, đừng từ chối hẳn — nếu không ta mất khả năng phân
            biệt "sửa được" với "sai hẳn" trong chính dữ liệu dùng để học. */}
        {reason === "thieu_can_cu" && (
          <div className="dim" style={{ fontSize: 12, marginTop: 8 }}>
            Nếu CSKH có thể bổ sung được căn cứ, hãy dùng <b>Yêu cầu điều tra thêm</b> ở
            màn chi tiết ticket thay vì từ chối — chỉ từ chối khi không thể bổ sung.
          </div>
        )}
        <div className="flex gap-sm wrap" style={{ marginTop: 12 }}>
          <button className="btn btn-danger-outline" disabled={busy || !reason} onClick={handleReject}>
            Xác nhận từ chối
          </button>
          <button className="btn btn-outline" disabled={busy} onClick={() => { setChonLyDo(false); setReason(""); }}>
            Huỷ
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-sm wrap" style={{ marginTop: 16 }}>
      <button className="btn btn-success" disabled={busy} onClick={handleRequestApprovalOtp}>
        <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5" /></svg>
        Duyệt
      </button>
      <button className="btn btn-danger-outline" disabled={busy} onClick={() => setChonLyDo(true)}>
        <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" /></svg>
        Từ chối
      </button>
    </div>
  );
}
