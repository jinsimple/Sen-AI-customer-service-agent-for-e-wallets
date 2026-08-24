"""Đếm tín hiệu theo HỘI THOẠI — primitive dùng chung, thiết kế MỘT LẦN.

Ba nơi cần đúng cùng một thứ (kế hoạch đợt 2, 15de5eb):
  · 5a ES-01  — bức xúc leo thang ≥N lượt LIÊN TIẾP
  · 5b lọc đầu ra — số lần một reply khớp nhóm O1–O4 trong cùng hội thoại
  · 5c guardrail — tín hiệu tích luỹ toàn hội thoại (Crescendo dò nhiều lượt)

Nhiều lần khớp trong MỘT hội thoại mới là tín hiệu, chứ một lần thì thường là
nhiễu — nên cả ba đều cần đếm theo hội thoại, không phải theo lượt.

BỐN LỰA CHỌN, mỗi cái trả giá ở đâu đó rồi mới rút ra
-----------------------------------------------------
1. REDIS, KHÔNG phải dict trong process. App chạy 4 uvicorn worker và một hội
   thoại KHÔNG đảm bảo rơi vào cùng worker — đúng cách vé WS từng hỏng ~3/4 số
   lần (QA-01). Bộ đếm trong RAM sẽ đếm nhầm theo cùng cơ chế đó, chỉ khác là
   nó không báo lỗi: nó chỉ đếm THIẾU, và ES-01 lặng lẽ không bao giờ bật.

2. CÓ TTL, đặt lại mỗi lần ghi. F-14 đã trả giá cho bài học này: bộ đếm không
   hạn vừa phình vô hạn vừa giữ trạng thái sai vĩnh viễn. 2 giờ ~ vòng đời một
   hội thoại; hết hạn thì hội thoại sau bắt đầu từ 0, đúng ý nghĩa mong muốn.

3. ĐƠN VỊ ĐẾM LÀ `thread_id`, KHÔNG phải `user_id`. `thread_id` = `user_id:iat`
   (ADR-007) nên đăng nhập phiên mới là hội thoại mới. Đếm theo `user_id` thì
   một khách bực hôm qua sẽ mang bộ đếm đó sang cuộc trò chuyện hôm nay —
   ES-01 bật vì chuyện đã xong, còn khách thì không hiểu vì sao.

4. FAIL-OPEN. Redis lỗi -> coi như KHÔNG có tín hiệu, hội thoại chạy bình
   thường. Ngược hẳn vé WS (fail-closed) và đây là chỗ dễ làm sai nhất: vé WS
   là CỬA VÀO nên nghi ngờ thì phải chặn; còn đếm tín hiệu chỉ để GỢI Ý và
   CẢNH BÁO, nên nghi ngờ thì phải cho qua. Một tính năng tiện ích không bao
   giờ được phép làm hỏng đường chính vì hạ tầng phụ của nó chết.
"""
from __future__ import annotations

import logging

from src.redis_client import get_default_client

_logger = logging.getLogger("fin05.thread_signals")

_KHOA = "fin05:thread_signal:"
# 2 giờ — rộng hơn một hội thoại thật, hẹp hơn một ca trực. Đặt lại mỗi lần ghi
# nên hội thoại đang diễn ra không bao giờ bị hết hạn giữa chừng.
TTL_GIAY = 2 * 3600


def _khoa(ten_tin_hieu: str, thread_id: str) -> str:
    return f"{_KHOA}{ten_tin_hieu}:{thread_id}"


def tang(ten_tin_hieu: str, thread_id: str) -> int:
    """Tăng bộ đếm, trả về giá trị sau khi tăng. Redis lỗi -> trả 0 (fail-open).

    Trả 0 chứ không raise: nơi gọi dùng giá trị này để so với ngưỡng, và 0 luôn
    dưới mọi ngưỡng ⟹ "không có tín hiệu". Nếu raise thì một sự cố Redis sẽ làm
    hỏng lượt chat của khách vì một tính năng phụ.
    """
    try:
        client = get_default_client()
        khoa = _khoa(ten_tin_hieu, thread_id)
        gia_tri = int(client.incr(khoa))
        # expire ĐẶT LẠI mỗi lần tăng: hội thoại còn hoạt động thì bộ đếm còn
        # sống; im lặng 2 tiếng thì tự dọn.
        client.expire(khoa, TTL_GIAY)
        return gia_tri
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_tang_that_bai",
            extra={"ten_tin_hieu": ten_tin_hieu, "thread_id": thread_id, "loi": repr(e)},
        )
        return 0


def doc(ten_tin_hieu: str, thread_id: str) -> int:
    """Đọc bộ đếm mà KHÔNG tăng. Redis lỗi -> 0 (fail-open)."""
    try:
        raw = get_default_client().get(_khoa(ten_tin_hieu, thread_id))
        return int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_doc_that_bai",
            extra={"ten_tin_hieu": ten_tin_hieu, "thread_id": thread_id, "loi": repr(e)},
        )
        return 0


def doc_hoac_khong_ro(ten_tin_hieu: str, thread_id: str) -> int | None:
    """Đọc bộ đếm — GIỐNG `doc()` khi Redis sống, KHÁC ở lúc Redis lỗi: trả
    `None` (KHÔNG ĐỌC ĐƯỢC) thay vì gộp chung với `0` (chưa có tín hiệu).

    🔴 Review bắt 24/08 (1B, cổng thu slot): `doc()` trả `0` cho CẢ "chưa
    hỏi" LẪN "Redis chết" — với ES-01/O1-O4/guardrail (ngưỡng-tích-luỹ),
    hướng đó ĐÚNG (0 luôn dưới ngưỡng, "không có tín hiệu" là hướng an
    toàn). Nhưng 1B dùng `doc()==0` để quyết "được phép bắn gate lần này
    không" — gộp "chưa hỏi" với "không biết" làm Redis chết ⟹ gate coi MỌI
    lượt là lần đầu ⟹ bắn LẶP LẠI thay vì tối đa một lần/hội thoại. Đúng
    câu mở đầu module này bị chính 1B vi phạm: "Sai an toàn = nghi ngờ thì
    đi ĐẦY ĐỦ" — không biết trạng thái phải đi `day_du`, không phải "chưa hỏi".

    KHÔNG đổi `doc()` — ba nơi gọi cũ (ES-01/O1-O4/guardrail) vẫn nhận
    đúng hợp đồng `int` cũ, không ai phải sửa theo. Hàm này CHỈ phục vụ
    nơi gọi cần phân biệt hai trạng thái đó để tự chọn hướng an toàn theo
    đúng tính năng của MÌNH — 1B là nơi đầu tiên cần, không phải nơi cuối."""
    try:
        raw = get_default_client().get(_khoa(ten_tin_hieu, thread_id))
        return int(raw) if raw else 0
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_doc_khong_ro",
            extra={"ten_tin_hieu": ten_tin_hieu, "thread_id": thread_id, "loi": repr(e)},
        )
        return None


def dat_lai(ten_tin_hieu: str, thread_id: str) -> None:
    """Xoá bộ đếm về 0.

    KHÔNG phải tiện ích dọn dẹp — đây là thứ làm nên ngữ nghĩa "LIÊN TIẾP" của
    ES-01. Không có nó thì đếm được là "tổng số lượt bực trong hội thoại", một
    thứ khác hẳn: khách bực 1 lượt, nguôi, bực lại, nguôi, bực lại vẫn chạm
    ngưỡng 3 — trong khi họ không hề leo thang. Nơi gọi PHẢI dat_lai() ở lượt
    KHÔNG mang tín hiệu, nếu không thì ngưỡng N mất hết ý nghĩa.
    """
    try:
        get_default_client().delete(_khoa(ten_tin_hieu, thread_id))
    except Exception as e:  # noqa: BLE001
        _logger.warning(
            "thread_signal_dat_lai_that_bai",
            extra={"ten_tin_hieu": ten_tin_hieu, "thread_id": thread_id, "loi": repr(e)},
        )
