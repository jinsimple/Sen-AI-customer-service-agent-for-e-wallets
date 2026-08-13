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

import { getCustomerHistory, requestOtp } from "@/lib/api";

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

describe("ChatClient — rail giao dịch gần đây", () => {
  it("hiện đúng giao dịch trả về từ getCustomerHistory", async () => {
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());
    expect(screen.getByText(/TXN20260810000001/)).toBeInTheDocument();
  });

  it("rail rỗng hiện đúng thông báo 'Chưa có giao dịch'", async () => {
    vi.mocked(getCustomerHistory).mockResolvedValue({ ...mockHistory, recent_transactions: [] });
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() => expect(screen.getByText("Chưa có giao dịch.")).toBeInTheDocument());
  });
});

describe("ChatClient — chip chọn loại khiếu nại", () => {
  it("bấm 'Báo lỗi giao dịch này' hiện đủ 4 chip loại khiếu nại", async () => {
    const user = userEvent.setup();
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Báo lỗi giao dịch này" }));

    for (const label of ["Chuyển nhầm", "Tiền chưa về", "Trừ tiền 2 lần", "Hoàn tiền"]) {
      expect(screen.getByText(label)).toBeInTheDocument();
    }
  });

  it("chọn 1 chip -> bắt đầu luồng OTP (khách CHƯA xác thực trong phiên)", async () => {
    const user = userEvent.setup();
    render(<ChatClient userId="USR-A" phone="0901000001" />);
    await waitFor(() => expect(screen.getByText(/92\.000đ/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "Báo lỗi giao dịch này" }));
    await user.click(screen.getByText("Tiền chưa về"));

    await waitFor(() => expect(requestOtp).toHaveBeenCalled());
    // AUTH5-01 (2026-08-12) — câu hỏi bảo mật đã bỏ khỏi vai trò xác thực,
    // form OTP chỉ còn hiện mã OTP mô phỏng.
    expect(await screen.findByText("123456")).toBeInTheDocument();
  });
});
