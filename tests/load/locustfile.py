"""Nhóm D — load/spike/soak/concurrency test (FIN05-StressTest-Plan.md D1-D3,
D6). Nhắm vào Next.js BFF (`/api/*`), KHÔNG gọi thẳng FastAPI — đúng kiến trúc
thật (trình duyệt/tester luôn đi qua BFF). Xem docs/TESTING.md để biết cách
chạy đầy đủ từng profile.

Chạy nhanh (debug locustfile, vài phút, không phải load test thật):
    locust -f tests/load/locustfile.py --host http://localhost:3000 \\
        --headless -u 10 -r 2 --run-time 2m

D1 — Load test (tăng dần tới điểm gãy):
    locust -f tests/load/locustfile.py --host <URL> --headless -u 100 -r 5 --run-time 10m

D2 — Spike test (dùng SpikeShape, không cần -u/-r tay):
    locust -f tests/load/locustfile.py --host <URL> --headless \\
        --class-picker SpikeShape   # hoặc chọn trong web UI (không --headless)

D3 — Soak test (tải vừa phải, chạy THẬT 1-2 giờ — chỉ chạy thủ công/nightly,
không chạy trong lúc dev bình thường):
    locust -f tests/load/locustfile.py --host <URL> --headless -u 20 -r 2 --run-time 2h

D6 — Concurrency cùng 1 ticket: set 2 biến môi trường trỏ vào 1 ticket/
resolution CÓ THẬT trong DB đang test (vd từ `scripts/seed_demo_scenarios.py`)
trước khi chạy, nếu không set thì task này tự bỏ qua (không làm hỏng cả run):
    TARGET_TICKET_ID=TCK-xxx TARGET_RESOLUTION_ID=RES-xxx locust -f tests/load/locustfile.py ...

LƯU Ý CHI PHÍ: CustomerUser gọi /api/agent-chat = gọi OpenAI thật mỗi request
— weight cố ý thấp. Muốn đo riêng tầng DB/API không lẫn độ trễ OpenAI, chạy
--tags cskh (loại CustomerUser) hoặc tăng weight CskhUser/SupervisorUser.
"""
from __future__ import annotations

import os
import pathlib
import random
import sys

# CỔNG ĐÓNG BĂNG — load test là thứ NGUY HIỂM NHẤT với trần TPM dùng chung:
# nó gọi /api/agent-chat theo tần suất, tức có thể làm cạn hạn mức của cả đội
# trong vài chục giây. Đo được 16/08: MỘT người, 21 lượt, 2 phút -> org chạm
# 193k/200k. Kiểm ở tầng IMPORT để locust chết ngay lúc nạp file, trước khi
# sinh ra user nào — bắt ở tầng task thì lượt đầu đã đi rồi.
_MOC = pathlib.Path(__file__).resolve().parent.parent.parent / ".DANG-DONG-BANG-LLM"
if _MOC.exists() or os.environ.get("FIN05_DONG_BANG_LLM", "").strip() not in ("", "0", "false"):
    sys.exit(
        f"🧊 ĐANG ĐÓNG BĂNG LLM — không chạy load test.\n"
        f"   Trần TPM dùng chung với 3 phiên khác + PO thật.\n"
        f"   Bỏ: unset FIN05_DONG_BANG_LLM · rm {_MOC.name}"
    )

from locust import HttpUser, LoadTestShape, between, task  # noqa: E402 — CỐ Ý sau cổng đóng băng ở trên

TARGET_TICKET_ID = os.environ.get("TARGET_TICKET_ID")
TARGET_RESOLUTION_ID = os.environ.get("TARGET_RESOLUTION_ID")

_CUSTOMER_PHONES = ["0387000001", "0761000002", "0812000003"]
_CSKH_PHONES = ["0353000201"]
_SUPERVISOR_PHONES = ["0905000205"]

_CHAT_MESSAGES = [
    "Phí rút tiền về ngân hàng là bao nhiêu vậy bạn?",
    "Tôi chuyển tiền mà bên kia chưa nhận được, kiểm tra giúp tôi với.",
    "Chính sách hoàn tiền của ví là gì vậy?",
    "Tôi bị trừ tiền 2 lần cho cùng 1 giao dịch, giúp tôi với.",
]


def _login(client, phone: str, role: str) -> bool:
    resp = client.post("/api/session", json={"phone": phone, "role": role}, name="/api/session [login]")
    return resp.status_code == 200


class CustomerUser(HttpUser):
    """D1/D3 — khách hàng chat với AI agent. CHẬM + TỐN vì gọi OpenAI thật
    mỗi request — weight thấp, đại diện tỉ lệ khách/nhân viên thực tế (nhiều
    khách hơn CSKH nhưng KHÔNG áp đảo để load test không quá đắt)."""

    weight = 2
    wait_time = between(3, 8)  # người thật gõ/đọc chậm hơn nhiều so với API call thuần

    def on_start(self):
        phone = random.choice(_CUSTOMER_PHONES)
        self.logged_in = _login(self.client, phone, "customer")

    @task
    def chat_with_agent(self):
        if not self.logged_in:
            return
        self.client.post(
            "/api/agent-chat", json={"message": random.choice(_CHAT_MESSAGES)}, name="/api/agent-chat"
        )


class CskhUser(HttpUser):
    """D1/D3 — CSKH tải dashboard/ticket liên tục. KHÔNG gọi LLM — nhanh, có
    thể tăng weight cao để đo riêng tầng DB/API."""

    weight = 5
    wait_time = between(1, 3)

    def on_start(self):
        phone = random.choice(_CSKH_PHONES)
        self.logged_in = _login(self.client, phone, "cskh")

    @task(3)
    def view_dashboard(self):
        if self.logged_in:
            self.client.get("/api/tickets?limit=50", name="/api/tickets")

    @task(2)
    def view_reports(self):
        if self.logged_in:
            self.client.get("/api/reports-summary", name="/api/reports-summary")

    @task(1)
    def search_policy(self):
        if self.logged_in:
            self.client.post("/api/policy-search", json={"query": "phí giao dịch"}, name="/api/policy-search")

    @task(1)
    def d6_concurrent_request_more_info(self):
        """D6 — 2+ CskhUser cùng thao tác 1 ticket cố định cùng lúc Supervisor
        approve (xem SupervisorUser.d6_concurrent_approve) — kiểm optimistic
        locking/race condition. Bỏ qua nếu chưa cấu hình TARGET_TICKET_ID."""
        if not self.logged_in or not TARGET_TICKET_ID:
            return
        self.client.post(
            f"/api/tickets/{TARGET_TICKET_ID}/request-more-info",
            json={"note": "load-test D6 concurrency probe"},
            name="/api/tickets/[id]/request-more-info [D6]",
        )


class SupervisorUser(HttpUser):
    """D1/D3 — Sếp xem/duyệt hàng chờ. Không gọi LLM."""

    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        phone = random.choice(_SUPERVISOR_PHONES)
        self.logged_in = _login(self.client, phone, "supervisor")

    @task(3)
    def view_pending_approvals(self):
        if self.logged_in:
            self.client.get("/api/resolutions?status=pending_approval", name="/api/resolutions")

    @task(1)
    def d6_concurrent_approve(self):
        """D6 — approve cùng 1 resolution trong lúc CskhUser đang sửa ticket
        liên quan (xem CskhUser.d6_concurrent_request_more_info). Backend
        (resolution.status not in draft/pending_approval -> 400) phải chặn
        approve kép — không được để 2 lần approve cùng thành công.

        AUTH5-04 (đợt nâng cấp Auth Flow 2026-08-12) — approve giờ cần OTP
        riêng cho ĐÚNG resolution_id, xin ngay trước mỗi lần gọi (không cache
        — mỗi actor ảo giả lập 1 lượt xin+duyệt độc lập, đúng luồng UI thật)."""
        if not self.logged_in or not TARGET_RESOLUTION_ID:
            return
        otp_resp = self.client.post(
            f"/api/resolutions/{TARGET_RESOLUTION_ID}/request-approval-otp",
            name="/api/resolutions/[id]/request-approval-otp [D6]",
        )
        if otp_resp.status_code != 200:
            return
        otp_body = otp_resp.json()
        self.client.post(
            f"/api/resolutions/{TARGET_RESOLUTION_ID}/approve",
            json={"session_id": otp_body.get("session_id", ""), "otp_code": otp_body.get("otp_code", "")},
            name="/api/resolutions/[id]/approve [D6]",
        )


class SpikeShape(LoadTestShape):
    """D2 — mô phỏng giờ cao điểm CSKH vào ca: tải thấp ổn định rồi tăng đột
    ngột trong thời gian ngắn rồi hạ về mức thường. Chọn shape này trong Locust
    web UI hoặc `--class-picker`, KHÔNG cần truyền -u/-r tay."""

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},  # baseline 1 phút
        {"duration": 90, "users": 100, "spawn_rate": 30},  # spike đột ngột (giờ CSKH vào ca)
        {"duration": 150, "users": 100, "spawn_rate": 5},  # giữ tải cao thêm 1 phút
        {"duration": 210, "users": 10, "spawn_rate": 10},  # hạ về baseline — quan sát hồi phục
    ]

    def tick(self):
        run_time = self.get_run_time()
        for stage in self.stages:
            if run_time < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None  # kết thúc test
