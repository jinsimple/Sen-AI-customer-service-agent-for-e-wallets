"use client";

import { useState } from "react";
import { ApiError, approveResolution, rejectResolution, requestResolutionApprovalOtp } from "@/lib/api";

/**
 * Cụm nút duyệt/từ chối MỘT đề xuất, kèm bước xin OTP.
 *
 * Tách ra dùng chung (hotfix 2, 14/08) vì cụm này giờ xuất hiện ở HAI nơi:
 * hàng chờ `/approve` và chi tiết ticket. Copy-paste hai bản là cách chắc
 * chắn nhất để một ngày nào đó chỉ một bản được vá — mà đây là đường đi tới
 * hành động chạm tiền, chỗ ít được phép lệch nhau nhất.
 *
 * AUTH5-04: duyệt cần OTP RIÊNG cho ĐÚNG resolution_id đang duyệt (PSD2
 * dynamic linking, gắn với đúng số tiền tại thời điểm xin mã). Môi trường
 * demo trả mã thẳng trong response nên hiện luôn cho sếp thấy, không bắt gõ
 * tay số đã biết sẵn — cùng cách luồng OTP của khách đang làm.
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
  const [otp, setOtp] = useState<{ sessionId: string; otpCode: string } | null>(null);

  async function handleRequestApprovalOtp() {
    setBusy(true);
    try {
      const res = await requestResolutionApprovalOtp(resolutionId);
      setOtp({ sessionId: res.session_id, otpCode: res.otp_code });
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Không xin được mã OTP duyệt");
    } finally {
      setBusy(false);
    }
  }

  async function handleConfirmApprove() {
    if (!otp) return;
    setBusy(true);
    try {
      await approveResolution(resolutionId, otp.sessionId, otp.otpCode);
      setOtp(null);
      await onDone();
    } catch (e) {
      onError(e instanceof ApiError ? e.message : "Duyệt thất bại");
    } finally {
      setBusy(false);
    }
  }

  async function handleReject() {
    setBusy(true);
    try {
      await rejectResolution(resolutionId);
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
          Mã OTP xác nhận duyệt: <strong className="mono approval-otp-code">{otp.otpCode}</strong>{" "}
          (còn hiệu lực 10 phút, chỉ dùng được cho đúng đề xuất này)
        </div>
        <div className="flex gap-sm wrap" style={{ marginTop: 8 }}>
          <button className="btn btn-success" disabled={busy} onClick={handleConfirmApprove}>
            Xác nhận duyệt
          </button>
          <button className="btn btn-outline" disabled={busy} onClick={() => setOtp(null)}>
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
      <button className="btn btn-danger-outline" disabled={busy} onClick={handleReject}>
        <svg className="icon icon-sm" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12" /></svg>
        Từ chối
      </button>
    </div>
  );
}
