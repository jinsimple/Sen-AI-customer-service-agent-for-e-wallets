import { render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import DashboardClient from "./DashboardClient";

/**
 * BUGREPRO-001/002 (FIN05_QA_TestCases.jsonl — QA/QC test tay 12/08/2026,
 * xác nhận lại bằng đọc code 13/08) — khách bấm "cho tôi gặp người thật",
 * CSKH đang mở sẵn Hàng chờ KHÔNG thấy gì.
 *
 * Nguyên nhân gốc: sự kiện WS `queue_update` chỉ gọi `loadWaitingChats()`.
 * Danh sách ticket — nguồn dữ liệu của bảng — chỉ fetch ĐÚNG MỘT LẦN lúc
 * mount (useEffect deps rỗng), và poll 60s cũng chỉ chạm `waitingChats`. Nên
 * bảng đứng yên tới khi reload cả trang.
 *
 * Test này canh đúng hành vi đó ở tầng component: bắn `queue_update` và
 * khẳng định `listTickets` được gọi LẠI, rồi ticket mới (có cờ handoff) xuất
 * hiện trên bảng.
 *
 * [polish trước quay 04/09] `listTickets` đổi shape từ mảng trần sang
 * `{items, total, page, page_size}` (phân trang thật) — mock cập nhật theo.
 * Chip "Khách yêu cầu người thật" cũng đổi từ đếm-số (đúng cửa sổ 100 vé,
 * nguồn gốc lỗi đọc-nhầm-% Lead bắt 20/08) sang toggle lọc-trang-này không
 * số — anchor cũ `\(0\//` không còn khớp, thay bằng khẳng định trực tiếp
 * trên DOM bảng (badge "Yêu cầu người thật" của đúng ticket mới).
 *
 * Mock ở biên module (`@/lib/api`, `useLiveChatSocket`, `next/navigation`) —
 * giữ nguyên hành vi render/state THẬT của React, cùng cách ChatClient.test.tsx.
 */

vi.mock("@/lib/api", () => ({
  listTickets: vi.fn(),
  claimTicket: vi.fn(),
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
    scope: "internal_wallet",
    priority: "normal",
    fraud_signals: [],
    customer_name: "Khách A",
    human_handoff_requested: false,
    claimed_by: null,
    ...overrides,
  };
}

function page(items: Record<string, unknown>[]) {
  return { items, total: items.length, page: 1, page_size: 50 };
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
    // Lượt đầu: chưa ai yêu cầu người thật. Lượt sau: đã có 1 khách yêu cầu.
    vi.mocked(listTickets)
      .mockResolvedValueOnce(page([ticket()]) as never)
      .mockResolvedValueOnce(
        page([
          ticket(),
          ticket({ ticket_id: "TCK-0002", human_handoff_requested: true, customer_name: "Khách B" }),
        ]) as never
      );

    render(<DashboardClient role="cskh" />);

    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));
    expect(screen.queryByText("Yêu cầu người thật")).toBeNull();

    // Khách bấm "gặp người thật" → backend broadcast queue_update.
    await waitFor(() => expect(capturedWsHandler).not.toBeNull());
    capturedWsHandler!({ type: "queue_update" });

    // Đây là điểm TRƯỚC BẢN VÁ sẽ đỏ: listTickets không bao giờ được gọi lần 2.
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Yêu cầu người thật")).toBeTruthy();
  });

  it("sự kiện session_claimed cũng nạp lại ticket (CSKH khác vừa nhận ca)", async () => {
    vi.mocked(listTickets).mockResolvedValue(page([ticket()]) as never);

    render(<DashboardClient role="cskh" />);
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));

    await waitFor(() => expect(capturedWsHandler).not.toBeNull());
    capturedWsHandler!({ type: "session_claimed" });

    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
  });

  it("sự kiện WS không liên quan KHÔNG được gây fetch thừa", async () => {
    vi.mocked(listTickets).mockResolvedValue(page([ticket()]) as never);

    render(<DashboardClient role="cskh" />);
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
    vi.mocked(listTickets).mockResolvedValue(page([ticket()]) as never);

    render(<DashboardClient role="cskh" />);
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(1));
    const waitingCallsBefore = vi.mocked(listWaitingChatSessions).mock.calls.length;

    await vi.advanceTimersByTimeAsync(60_000);

    // Trước bản vá: chỉ waitingChats được poll, ticket đứng yên vô thời hạn
    // mà không có dấu hiệu nào cho CSKH biết dữ liệu đã cũ.
    await waitFor(() => expect(listTickets).toHaveBeenCalledTimes(2));
    expect(vi.mocked(listWaitingChatSessions).mock.calls.length).toBeGreaterThan(waitingCallsBefore);
  });
});
