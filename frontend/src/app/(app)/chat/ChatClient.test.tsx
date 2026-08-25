import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import ChatClient from "./ChatClient";

/**
 * FIN05-StressTest-Plan-v4 F4-05 — component test cho state phức tạp trong
 * ChatClient.tsx (chip chọn loại khiếu nại + rail "Giao dịch gần đây") —
 * dùng React Testing Library, KHÔNG cần trình duyệt thật (Playwright) cho
 * lớp logic UI này. Mock `@/lib/api` + `useLiveChatSocket` ở biên module —
 * không mock React/DOM, giữ hành vi render/state THẬT.
 */

vi.mock("@/lib/api", () => ({
  ApiError: class ApiError extends Error {},
  agentChat: vi.fn(),
  getCustomerHistory: vi.fn(),
  requestLiveChatWsTicket: vi.fn(),
  requestOtp: vi.fn(),
  verifyOtp: vi.fn(),
}));

vi.mock("@/lib/useLiveChatSocket", () => ({
  useLiveChatSocket: vi.fn(() => ({ status: "idle", sendMessage: vi.fn() })),
}));

import { agentChat, getCustomerHistory, requestOtp, verifyOtp } from "@/lib/api";

const mockHistory = {
  user_id: "USR-A",
  kyc_level: 2,
  wallets: [],
  recent_transactions: [
    {
      trans_id: "TXN20260810000001",
      amount: 92_000,
      status: "success",
      scope: "internal_wallet" as const,
      direction: "out" as const,
      created_at: "2026-08-10T09:00:00Z",
    },
  ],
  complaint_count_90d: 0,
  complaints: [],
  tool_result_id: "TR-mock-001",
};

beforeEach(() => {
  vi.mocked(getCustomerHistory).mockResolvedValue(mockHistory);
  vi.mocked(requestOtp).mockResolvedValue({
    session_id: "SES-mock-001",
    security_question: "Tên đệm của mẹ bạn là gì?",
    otp_code: "123456",
    note: "mock — không dùng trong test này",
  });
});

afterEach(() => {
  vi.clearAllMocks();
});

// V6 (hotfix 14/08, PO đổi chính sách): rail "Giao dịch gần đây" BỊ CHE cho
// tới khi khách xác thực OTP trong phiên. Ba test dưới đây từng giả định rail
// hiện ngay khi vào trang — giả định đó nay sai, nên chúng được viết lại quanh
// hành vi mới thay vì nới lỏng assert.
/** Đi trọn luồng OTP trong phiên: bấm "Xác thực ngay" -> điền 6 ô mã.
 *  Sau bước này rail "Giao dịch gần đây" mới hiện (V6). Lỗi 12 (PO thật
 *  19/08): thẻ "Lịch sử khiếu nại" giờ CŨNG có nút "Xác thực ngay" riêng
 *  (cùng khuôn thẻ giao dịch) -> `findAllByRole`, bấm nút ĐẦU vẫn đủ vì cả
 *  hai thẻ dùng CHUNG state `otpVerified`, một lần xác thực mở cả hai. */
async function xacThucOtpTrongPhien(user: ReturnType<typeof userEvent.setup>) {
  const nutXacThuc = await screen.findAllByRole("button", { name: "Xác thực ngay" });
  await user.click(nutXacThuc[0]);
  await waitFor(() => expect(document.querySelectorAll("input.otp-box").length).toBe(6));
  const o = Array.from(document.querySelectorAll("input.otp-box")) as HTMLInputElement[];
  for (let i = 0; i < 6; i++) await user.type(o[i], "123456"[i]);
  await user.click(screen.getByRole("button", { name: "Xác nhận" }));
  await waitFor(() => expect(verifyOtp).toHaveBeenCalled());
}

describe("ChatClient — rail giao dịch gần đây", () => {
  it("CHƯA xác thực OTP thì che danh sách, hiện lời mời xác thực", async () => {
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    await waitFor(() =>
      expect(screen.getByText("Xác thực OTP để xem giao dịch gần đây")).toBeInTheDocument()
    );
    expect(screen.queryByText(/92\.000đ/)).not.toBeInTheDocument();
    // Lỗi 12 (PO thật 19/08): thẻ "Lịch sử khiếu nại" giờ CŨNG có nút riêng
    // cùng tên — getAllByRole thay vì getByRole (uniqueness không phải thứ
    // test này kiểm, chỉ kiểm "nút xác thực CÓ mặt").
    expect(screen.getAllByRole("button", { name: "Xác thực ngay" }).length).toBeGreaterThan(0);
  });

  it("rail rỗng: vẫn che trước khi xác thực (không lộ 'Chưa có giao dịch')", async () => {
    vi.mocked(getCustomerHistory).mockResolvedValue({ ...mockHistory, recent_transactions: [] });
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    await waitFor(() =>
      expect(screen.getByText("Xác thực OTP để xem giao dịch gần đây")).toBeInTheDocument()
    );
    expect(screen.queryByText("Chưa có giao dịch.")).not.toBeInTheDocument();
  });
});

// Lỗi 12 (PO thật 19/08, docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md
// mục 12) — thẻ "Lịch sử khiếu nại" từng KHÔNG có cổng OTP dù thẻ "Giao
// dịch gần đây" cạnh nó có, dù CÙNG mức nhạy cảm dữ liệu (loại/trạng thái
// khiếu nại). Hai ca dưới khoá lại hành vi ĐÃ VÁ bằng `RailCardGatedByOtp`.
describe("ChatClient — rail lịch sử khiếu nại (Lỗi 12)", () => {
  const mockHistoryCoKhieuNai = {
    ...mockHistory,
    complaints: [
      { complaint_id: "CMP-mock-001", type: "double_charge" as const, status: "investigating", created_at: "2026-08-11T09:00:00Z" },
    ],
  };

  it("CHƯA xác thực OTP thì che lịch sử khiếu nại, hiện lời mời xác thực", async () => {
    vi.mocked(getCustomerHistory).mockResolvedValue(mockHistoryCoKhieuNai);
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    await waitFor(() =>
      expect(screen.getByText("Xác thực OTP để xem lịch sử khiếu nại")).toBeInTheDocument()
    );
    expect(screen.queryByText("CMP-mock-001")).not.toBeInTheDocument();
  });

  it("đã xác thực OTP -> lịch sử khiếu nại hiện đúng dữ liệu", async () => {
    const user = userEvent.setup();
    vi.mocked(getCustomerHistory).mockResolvedValue(mockHistoryCoKhieuNai);
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    await xacThucOtpTrongPhien(user);
    await waitFor(() => expect(screen.getByText("CMP-mock-001")).toBeInTheDocument());
    // Nhãn loại khiếu nại nằm chung 1 div với dấu "·"+ngày (nhiều text node
    // con) — badge trạng thái ở span riêng, node đơn, an toàn để so khớp.
    expect(screen.getByText("Đang xử lý")).toBeInTheDocument();
  });
});

describe("ChatClient — chip chọn loại khiếu nại", () => {
  it("bấm 'Báo lỗi giao dịch này' hiện đủ 4 chip loại khiếu nại", async () => {
    const user = userEvent.setup();
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    // V6: nút "Báo lỗi giao dịch này" nằm trong rail, mà rail bị che tới khi
    // xác thực xong — nên phải qua OTP trước.
    await xacThucOtpTrongPhien(user);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Báo lỗi giao dịch này" }));

    for (const label of ["Chuyển nhầm", "Tiền chưa về", "Trừ tiền 2 lần", "Hoàn tiền"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("đã xác thực trong phiên -> chọn chip gửi thẳng agent, không hỏi OTP lần hai", async () => {
    const user = userEvent.setup();
    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);
    await xacThucOtpTrongPhien(user);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Báo lỗi giao dịch này" }));
    await user.click(screen.getByText("Tiền chưa về"));

    // Đã xác thực trong phiên -> KHÔNG hỏi OTP lần hai, gửi thẳng cho agent.
    await waitFor(() => expect(agentChat).toHaveBeenCalled());
    expect(requestOtp).toHaveBeenCalledTimes(1);
  });
});

// Lỗi 1 (PO thật tự bắt 19/08, docs/giao-viec/2026-08-19-gd4-po-test-4-loi-ui.md
// mục 2) — câu hỏi TỰ DO (không qua chip/rail) chạm dữ liệu nhạy cảm lần đầu
// trong phiên bị đòi OTP xen giữa; trước bản vá, `pendingStarterRef` không
// được set ở nhánh này (khác 2 nhánh kia đã có sẵn từ Finding B GĐ2.5) nên
// câu khách vừa hỏi bị MẤT sau khi xác thực xong — khách phải gõ lại.
describe("ChatClient — OTP xen giữa câu hỏi tự do (Lỗi 1)", () => {
  it("câu tự do chạm dữ liệu nhạy cảm -> đòi OTP -> sau khi xác thực TỰ GỬI LẠI đúng câu cũ", async () => {
    const user = userEvent.setup();
    const CAU = "cho tôi kiểm tra giao dịch TXN20260810000001";
    vi.mocked(agentChat)
      .mockResolvedValueOnce({
        reply: "Để tra được, mình cần xác thực OTP trước.",
        tool_calls: [
          { tool_name: "lookup_transaction", args: {}, result: { status: "error" } },
        ],
        ticket_id: null,
        should_escalate: false,
      })
      .mockResolvedValueOnce({
        reply: "Giao dịch TXN20260810000001 đã xử lý thành công.",
        tool_calls: [
          { tool_name: "lookup_transaction", args: {}, result: { status: "found" } },
        ],
        ticket_id: null,
        should_escalate: false,
      });

    render(<ChatClient userId="USR-A" phone="0901000001" otpXemConHanLucTai={false} />);

    await user.type(screen.getByPlaceholderText("Nhập tin nhắn..."), CAU);
    await user.click(screen.getByRole("button", { name: "Gửi tin nhắn" }));

    await waitFor(() => expect(document.querySelectorAll("input.otp-box").length).toBe(6));
    const o = Array.from(document.querySelectorAll("input.otp-box")) as HTMLInputElement[];
    for (let i = 0; i < 6; i++) await user.type(o[i], "123456"[i]);
    await user.click(screen.getByRole("button", { name: "Xác nhận" }));

    // Sau khi OTP xanh, agentChat phải được gọi LẦN HAI với ĐÚNG câu cũ —
    // KHÔNG cần khách gõ lại (đây là điều bản vá đảm bảo).
    await waitFor(() => expect(agentChat).toHaveBeenCalledTimes(2));
    // 🔴 CHẶT HƠN bản cũ, không phải nới ra: bản cũ chờ đúng `{message}`, nên
    // nó ĐỎ từ a663583 (24/08) — commit thêm cờ `vua_xac_thuc_de_gui_lai`.
    // Cờ ấy PHẢI là `true` ở đây theo thiết kế: đây đúng là một trong ba nguồn
    // đặt `pendingStarterRef` (touchedSensitiveData), tức lượt TỰ GỬI LẠI câu
    // đã bị cổng OTP chặn. Khẳng định nó = ghim luôn ngữ nghĩa gửi-lại, thứ
    // bản cũ không kiểm được.
    expect(vi.mocked(agentChat).mock.calls[1][0]).toEqual({
      message: CAU,
      vua_xac_thuc_de_gui_lai: true,
    });
    // Câu cũ chỉ hiện MỘT LẦN trong khung chat (không hiện lại như tin nhắn
    // mới của khách) — sendToAgent gọi với echoAsUser:false cho lượt tự gửi.
    expect(screen.getAllByText(CAU)).toHaveLength(1);
  });
});
