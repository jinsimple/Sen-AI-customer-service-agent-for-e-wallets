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
 *  Sau bước này rail "Giao dịch gần đây" mới hiện (V6). */
async function xacThucOtpTrongPhien(user: ReturnType<typeof userEvent.setup>) {
  await user.click(await screen.findByRole("button", { name: "Xác thực ngay" }));
  await waitFor(() => expect(document.querySelectorAll("input.otp-box").length).toBe(6));
  const o = Array.from(document.querySelectorAll("input.otp-box")) as HTMLInputElement[];
  for (let i = 0; i < 6; i++) await user.type(o[i], "123456"[i]);
  await user.click(screen.getByRole("button", { name: "Xác nhận" }));
  await waitFor(() => expect(verifyOtp).toHaveBeenCalled());
}

describe("ChatClient — rail giao dịch gần đây", () => {
  it("CHƯA xác thực OTP thì che danh sách, hiện lời mời xác thực", async () => {
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() =>
      expect(screen.getByText("Xác thực OTP để xem giao dịch gần đây")).toBeInTheDocument()
    );
    expect(screen.queryByText(/92\.000đ/)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Xác thực ngay" })).toBeInTheDocument();
  });

  it("rail rỗng: vẫn che trước khi xác thực (không lộ 'Chưa có giao dịch')", async () => {
    vi.mocked(getCustomerHistory).mockResolvedValue({ ...mockHistory, recent_transactions: [] });
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() =>
      expect(screen.getByText("Xác thực OTP để xem giao dịch gần đây")).toBeInTheDocument()
    );
    expect(screen.queryByText("Chưa có giao dịch.")).not.toBeInTheDocument();
  });
});

describe("ChatClient — chip chọn loại khiếu nại", () => {
  it("bấm 'Báo lỗi giao dịch này' hiện đủ 4 chip loại khiếu nại", async () => {
    const user = userEvent.setup();
    render(<ChatClient userId="USR-A" phone="0901000001" />);
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
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await xacThucOtpTrongPhien(user);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Báo lỗi giao dịch này" }));
    await user.click(screen.getByText("Tiền chưa về"));

    // Đã xác thực trong phiên -> KHÔNG hỏi OTP lần hai, gửi thẳng cho agent.
    await waitFor(() => expect(agentChat).toHaveBeenCalled());
    expect(requestOtp).toHaveBeenCalledTimes(1);
  });
});
