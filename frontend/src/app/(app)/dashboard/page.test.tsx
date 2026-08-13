import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DashboardPage from "./page";

/**
 * BUGREPRO-001/002 (FIN05_QA_TestCases.jsonl — QA/QC test tay 12/08/2026,
 * xác nhận lại bằng đọc code 13/08) — khách bấm "cho tôi gặp người thật",
 * CSKH đang mở sẵn Hàng chờ KHÔNG thấy gì, chip "Khách yêu cầu người thật (N)"
 * đứng yên ở 0.
 *
 * Nguyên nhân gốc: sự kiện WS `queue_update` chỉ gọi `loadWaitingChats()`.
 * Danh sách `tickets` — nguồn dữ liệu của MỌI chip đếm và của cả bảng ticket —
 * chỉ fetch ĐÚNG MỘT LẦN lúc mount (useEffect deps rỗng), và poll 60s cũng chỉ
 * chạm `waitingChats`. Nên số đếm đứng yên tới khi reload cả trang.
 *
 * Test này canh đúng hành vi đó ở tầng component: bắn `queue_update` và khẳng
 * định `listTickets` được gọi LẠI, rồi chip đếm lên đúng số mới.
 *
 * Mock ở biên module (`@/lib/api`, `useLiveChatSocket`, `next/navigation`) —
 * giữ nguyên hành vi render/state THẬT của React, cùng cách ChatClient.test.tsx.
 */

vi.mock("@/lib/api", () => ({
  listTickets: vi.fn(),
  listWaitingChatSessions: vi.fn(),
  requestStaffWsTicket: vi.fn(),
}));

// Giữ lại handler mà component đăng ký, để test tự bắn sự kiện WS vào.
let capturedWsHandler: ((event: { type: string }) => void) | null = null;
vi.mock("@/lib/useLiveChatSocket", () => ({
  useLiveChatSocket: vi.fn((_ticket: string | null, handler: (e: { type: string }) => void) => {
    capturedWsHandler = handler;
    return { status: "idle", sendMessage: vi.fn() };
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn(), refresh: vi.fn() }),
}));

import { listTickets, listWaitingChatSessions, requestStaffWsTicket } from "@/lib/api";

function ticket(overrides: Record<string, unknown> = {}) {
  return {
    ticket_id: "TCK-0001",
    complaint_id: "CMP-0001",
    hitl_status: "pending",
    sla_due_at: "2026-09-12T08:00:00Z",
    partner_wait_status: "n/a",
    created_at: "2026-08-13T08:00:00Z",
    complaint_type: "other",
    scope: "unknown",
    priority: "normal",
    fraud_signals: [],
    customer_name: "Khách A",
    human_handoff_requested: false,
    ...overrides,
  };
}

describe("Dashboard — hàng chờ cập nhật khi có khách yêu cầu người thật", () => {
  beforeEach(() => {
    capturedWsHandler = null;
    vi.mocked(listWaitingChatSessions).mockResolvedValue({ sessions: [] });
    vi.mocked(requestStaffWsTicket).mockResolvedValue({ ws_ticket: "WST-test" });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  it("BUGREPRO-002: sự kiện queue_update phải nạp LẠI danh sách ticket, không chỉ waitingChats", async () => {
    // Lượt đầu: chưa ai yêu cầu người thật → chip = 0.
    // Lượt sau: đã có 1 khách yêu cầu → chip phải thành 1.
    vi.mocked(listTickets)
      .mockResolvedValueOnce([ticket()] as never)
      .mockResolvedValueOnce([
        ticket(),
        ticket({ ticket_id: "TCK-0002", human_handoff_requested: true, customer_name: "Khách B" }),
      ] as never);

    render(<DashboardPage />);

    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/Khách yêu cầu người thật \(0\)/)).toBeTruthy();

    // Khách bấm "gặp người thật" → backend broadcast queue_update.
    await waitFor(() => expect(capturedWsHandler).not.toBeNull());
    capturedWsHandler!({ type: "queue_update" });

    // Đây là điểm TRƯỚC BẢN VÁ sẽ đỏ: listTickets không bao giờ được gọi lần 2.
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
    expect(await screen.findByText(/Khách yêu cầu người thật \(1\)/)).toBeTruthy();
  });

  it("sự kiện session_claimed cũng nạp lại ticket (CSKH khác vừa nhận ca)", async () => {
    vi.mocked(listTickets).mockResolvedValue([ticket()] as never);

    render(<DashboardPage />);
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));

    await waitFor(() => expect(capturedWsHandler).not.toBeNull());
    capturedWsHandler!({ type: "session_claimed" });

    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
  });

  it("sự kiện WS không liên quan KHÔNG được gây fetch thừa", async () => {
    vi.mocked(listTickets).mockResolvedValue([ticket()] as never);

    render(<DashboardPage />);
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));

    await waitFor(() => expect(capturedWsHandler).not.toBeNull());
    capturedWsHandler!({ type: "message" });

    // Chờ một nhịp rồi khẳng định KHÔNG có lần gọi thứ 2 — chống bản vá quá
    // tay kiểu "cứ có event là fetch lại tất", gây bão request khi chat sôi nổi.
    await new Promise((r) => setTimeout(r, 50));
    expect(listTickets).toHaveBeenCalledTimes(1);
  });

  it("lưới an toàn 60s nạp lại CẢ ticket lẫn waitingChats khi WS rớt", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    vi.mocked(listTickets).mockResolvedValue([ticket()] as never);

    render(<DashboardPage />);
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));
    const waitingCallsBefore = vi.mocked(listWaitingChatSessions).mock.calls.length;

    await vi.advanceTimersByTimeAsync(60_000);

    // Trước bản vá: chỉ waitingChats được poll, ticket đứng yên vô thời hạn
    // mà không có dấu hiệu nào cho CSKH biết dữ liệu đã cũ.
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
    expect(vi.mocked(listWaitingChatSessions).mock.calls.length).toBeGreaterThan(waitingCallsBefore);
  });
});
