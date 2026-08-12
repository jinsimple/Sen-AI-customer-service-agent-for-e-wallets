import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useLiveChatSocket, type LiveChatEvent } from "./useLiveChatSocket";

/**
 * FIN05-StressTest-Plan-v4 L4-09/F4-04 — `useLiveChatSocket.ts` (reconnect,
 * status derive, gửi/nhận) hoàn toàn CHƯA có test tự động nào (gap doc
 * §3, "0% unit test frontend"). jsdom KHÔNG có WebSocket thật — tự viết
 * mock tối giản mô phỏng đúng lifecycle (onopen/onmessage/onclose/onerror)
 * mà hook thật dùng, KHÔNG mock toàn bộ hành vi mạng thật (đủ để test
 * ĐÚNG logic của hook, không phải test trình duyệt/mạng).
 */

class MockWebSocket {
  // Hook thật so sánh readyState với WebSocket.OPEN (hằng số tĩnh chuẩn,
  // giá trị 1) — global WebSocket đã bị stub bằng class này, nếu không tự
  // khai lại các hằng số tĩnh, WebSocket.OPEN sẽ là undefined, khiến MỌI so
  // sánh readyState !== WebSocket.OPEN luôn đúng (false-negative im lặng).
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSING = 2;
  static readonly CLOSED = 3;
  static instances: MockWebSocket[] = [];
  url: string;
  readyState = 0; // CONNECTING
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((evt: { data: string }) => void) | null = null;
  sent: string[] = [];
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    if (this.readyState !== 1) throw new Error("WebSocket chưa mở, không gửi được (mô phỏng hành vi thật)");
    this.sent.push(data);
  }

  close() {
    this.closed = true;
    this.readyState = 3; // CLOSED
    this.onclose?.();
  }

  // Helper test-only — mô phỏng server accept kết nối.
  simulateOpen() {
    this.readyState = 1; // OPEN
    this.onopen?.();
  }

  simulateMessage(payload: unknown) {
    this.onmessage?.({ data: JSON.stringify(payload) });
  }

  simulateRawMessage(raw: string) {
    this.onmessage?.({ data: raw });
  }

  simulateServerClose() {
    this.readyState = 3;
    this.onclose?.();
  }
}

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket as unknown as typeof WebSocket);
  // CHỈ patch window.location — stub cả `window` (như bản đầu viết) xoá mất
  // DOM thật của jsdom, làm @testing-library/react không tìm được container
  // ("Expected container to be an Element...got undefined").
  vi.stubGlobal("location", { ...window.location, protocol: "https:", host: "localhost" });
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("useLiveChatSocket", () => {
  it("status = 'idle' khi chưa có wsTicket, không tạo WebSocket nào", () => {
    const { result } = renderHook(() => useLiveChatSocket(null, () => {}));
    expect(result.current.status).toBe("idle");
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("status = 'connecting' ngay khi có wsTicket, trước khi server accept", () => {
    const { result } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    expect(result.current.status).toBe("connecting");
    expect(MockWebSocket.instances).toHaveLength(1);
  });

  it("URL kết nối dùng đúng protocol (wss cho https) + đúng vé trong query param", () => {
    renderHook(() => useLiveChatSocket("ticket-xyz", () => {}));
    expect(MockWebSocket.instances[0].url).toBe("wss://localhost/ws/live-chat?ticket=ticket-xyz");
  });

  it("status = 'open' sau khi server accept (onopen)", async () => {
    const { result } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    act(() => MockWebSocket.instances[0].simulateOpen());
    await waitFor(() => expect(result.current.status).toBe("open"));
  });

  it("status = 'closed' khi kết nối đóng", async () => {
    const { result } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    act(() => MockWebSocket.instances[0].simulateOpen());
    act(() => MockWebSocket.instances[0].simulateServerClose());
    await waitFor(() => expect(result.current.status).toBe("closed"));
  });

  it("gọi onEvent với payload đã parse JSON khi nhận message hợp lệ", () => {
    const onEvent = vi.fn<(e: LiveChatEvent) => void>();
    renderHook(() => useLiveChatSocket("ticket-abc", onEvent));
    const event: LiveChatEvent = { type: "system", text: "xin chào" };
    act(() => MockWebSocket.instances[0].simulateMessage(event));
    expect(onEvent).toHaveBeenCalledWith(event);
  });

  it("KHÔNG crash / KHÔNG gọi onEvent khi nhận frame không phải JSON hợp lệ", () => {
    const onEvent = vi.fn();
    renderHook(() => useLiveChatSocket("ticket-abc", onEvent));
    expect(() => act(() => MockWebSocket.instances[0].simulateRawMessage("khong-phai-json{{{"))).not.toThrow();
    expect(onEvent).not.toHaveBeenCalled();
  });

  it("sendMessage trả false và KHÔNG gửi gì nếu socket chưa mở", () => {
    const { result } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    // Chưa simulateOpen() — readyState vẫn CONNECTING.
    // Gọi TRỰC TIẾP (không bọc act()) — sendMessage không setState nào cả,
    // chỉ đọc ref + gọi ws.send(), bọc act() ở đây chỉ khiến React 19 trả về
    // 1 thenable thay vì giá trị boolean thật (phải await mới lấy ra được).
    const sent = result.current.sendMessage("CHS-1", "chào bạn");
    expect(sent).toBe(false);
    expect(MockWebSocket.instances[0].sent).toHaveLength(0);
  });

  it("sendMessage trả true và gửi đúng payload {type, chat_session_id, content} khi đã mở", () => {
    const { result } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    act(() => MockWebSocket.instances[0].simulateOpen());
    const sent = result.current.sendMessage("CHS-1", "chào bạn");
    expect(sent).toBe(true);
    expect(JSON.parse(MockWebSocket.instances[0].sent[0])).toEqual({
      type: "send_message",
      chat_session_id: "CHS-1",
      content: "chào bạn",
    });
  });

  it("unmount đóng kết nối WebSocket (không để lại kết nối mồ côi)", () => {
    const { unmount } = renderHook(() => useLiveChatSocket("ticket-abc", () => {}));
    act(() => MockWebSocket.instances[0].simulateOpen());
    unmount();
    expect(MockWebSocket.instances[0].closed).toBe(true);
  });

  it("đổi wsTicket -> đóng kết nối CŨ, mở kết nối MỚI với vé mới", () => {
    const { rerender } = renderHook(({ ticket }: { ticket: string }) => useLiveChatSocket(ticket, () => {}), {
      initialProps: { ticket: "ticket-1" },
    });
    const first = MockWebSocket.instances[0];
    act(() => first.simulateOpen());

    rerender({ ticket: "ticket-2" });

    expect(first.closed).toBe(true);
    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toContain("ticket-2");
  });
});
