"""🔴 BẤT BIẾN NGHIỆP VỤ: một lượt chat không bao giờ sinh > 1 hồ sơ khiếu nại.

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI** — bộ này điều khiển container qua
> `docker exec`. Chạy bên trong container thì `FileNotFoundError: docker`.
> ✅ **0 lượt LLM** — không tốn token.

    hai lời gọi `create_ticket` trong CÙNG MỘT lượt  ⟹  ≤ 1 complaint

## Vì sao bất biến này tồn tại, và vì sao nó đang ĐỎ

17/08, ba vòng đo R cho thấy model gọi `create_ticket` **hai lần trong một
lượt** (R1, R2). Mô tả tool nói nguyên văn *"bước CUỐI CÙNG của quy trình, gọi
**ĐÚNG MỘT LẦN** cho mỗi khiếu nại"* — chỉ dẫn rõ, không mâu thuẫn với gì khác,
và model vẫn vi phạm. **Chỗ này không sửa được bằng cách thêm chữ.**

Đội tin rằng *"chống-trùng tầng code gánh"* — vì R1/R2 chỉ sinh **một** vé dù
gọi hai lần. Tôi đo, và **cơ chế đó không tồn tại**:

    CÙNG `TurnGuard`, cùng tham số, gọi 2 lần  →  Δcomplaints = 2 · Δtickets = 2
    KHÁC `TurnGuard`, cùng tham số, gọi 2 lần  →  Δcomplaints = 2 · Δtickets = 2

Coder xác nhận từ phía mã, ba nơi: không `UniqueConstraint` trên `complaints` ·
`create_ticket_with_fraud_check` không truy vấn khiếu nại cũ · `TurnGuard` chỉ
chặn nhánh `abandoned`.

> **Một giảm nhẹ chưa ai đo là một giảm nhẹ chưa tồn tại** — và nó nguy hơn
> không có giảm nhẹ nào, vì nó làm finding gốc bị hạ hạng. Ở đây nó đã hạ hạng
> finding "gọi hai lần" xuống thành "chỉ tốn một dòng log", suốt một buổi.

**Hậu quả thật:** hai hồ sơ khiếu nại vào hàng chờ CSKH cho **một** sự việc, và
khách chỉ được báo **một** mã vé. Vé thứ hai là một khiếu nại **không ai nhận**.

## Vì sao đo ở TẦNG TOOL chứ không qua `/agent/chat`

Model gọi hai lần hay một lần là **ngẫu nhiên** (R3 chỉ gọi một). Một test gửi
lượt chat rồi kiểm `Δ ≤ 1` sẽ **xanh phần lớn thời gian** — tức nó canh một
điều nó không kiểm được, đúng thứ Luật 1 cấm.

Ở tầng tool thì tiền đề *"hai lời gọi trong một lượt"* **dựng được tất định**,
và bất biến trở thành một mệnh đề kiểm được: *cho hai lời gọi, hệ phải sinh ≤1
hồ sơ.* Đây là chỗ bất biến **thi hành được**, không phải chỗ nó bị vi phạm.

## Không để lại dấu vết — đo được, không phải tin

Tool **không tự commit** (kiểm 17/08: gọi rồi `rollback()`, số hàng về nguyên).
Nên test đếm **trong giao dịch chưa commit** rồi lăn ngược ⟹ `Δ` thật = 0 trên
đĩa. Đây là điều kiện ④ của Luật 15 được thoả **bằng kiến trúc**, không bằng
một bước dọn phải nhớ chạy.
"""
from __future__ import annotations

import json
import subprocess

import pytest

from tests._docker_co_mat import co_docker

CT = "fin05do-backend-1"


def _stack_song() -> bool:
    # 🔴 CHẶN TRƯỚC: hàm này chạy trong biểu thức `skipif`, tức LÚC IMPORT.
    # Máy không có `docker` thì `subprocess` ném FileNotFoundError trong lúc
    # pytest THU THẬP ⟹ `Interrupted`, và kết quả của MỌI ca khác biến mất.
    # Đo được 18/08: 634 ca thu thập được → 0 ca chạy, chỉ vì thiếu một tệp
    # nhị phân. Trạng thái đúng là SKIP KÈM LÝ DO, không phải 'tệp này hỏng'.
    if not co_docker():
        return False
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={CT}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = pytest.mark.skipif(
    not _stack_song(),
    reason=f"cần ngăn xếp ĐO DÙNG RIÊNG {CT} — test này gọi tool GHI (dù lăn "
           "ngược), không chạy trên ngăn xếp dùng chung (Luật 15)",
)

_MA = r'''
import json, time
from src.db.session import SessionLocal
from src.db.models import Complaint, Ticket
from src.agents.tools.customer_tools import build_customer_tools as B, TurnGuard

s = SessionLocal()
truoc = (s.query(Complaint).count(), s.query(Ticket).count())
g = TurnGuard()
ct = [x for x in B(s, user_id="USR-0001", otp_verified_at=time.time(), guard=g)
      if x.name == "create_ticket"][0]
args = {"complaint_type": "money_not_received", "scope": "unknown",
        "description_raw": "[DO-LUONG bat-bien-mot-luot] khong phai khieu nai that"}
r1 = ct.invoke(args)
r2 = ct.invoke(args)
sau = (s.query(Complaint).count(), s.query(Ticket).count())
s.rollback()          # KHÔNG commit — không để lại dấu vết trên đĩa
s.close()
s2 = SessionLocal(); dia = (s2.query(Complaint).count(), s2.query(Ticket).count()); s2.close()
print(json.dumps({
    "d_complaint": sau[0] - truoc[0], "d_ticket": sau[1] - truoc[1],
    "con_lai_tren_dia": [dia[0] - truoc[0], dia[1] - truoc[1]],
    "ve": [(r.get("ticket_id") if isinstance(r, dict) else None) for r in (r1, r2)],
    "trang_thai": [(r.get("status") if isinstance(r, dict) else None) for r in (r1, r2)],
}, ensure_ascii=False))
'''


@pytest.fixture(scope="module")
def hai_loi_goi() -> dict:
    r = subprocess.run(["docker", "exec", CT, "python", "-c", _MA],
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, f"probe hỏng: {(r.stderr or r.stdout)[-400:]}"
    return json.loads(r.stdout.strip().splitlines()[-1])


def test_KHONG_de_lai_dau_vet_tren_dia(hai_loi_goi):
    """Điều kiện tiên quyết — test này GHI, nên nó phải tự chứng minh đã lăn ngược.

    Đặt TRƯỚC bất biến chính, vì nếu nó hỏng thì mỗi lần chạy test lại bơm thêm
    hai hồ sơ khiếu nại vào CSDL — công cụ kiểm trở thành thứ nó đi kiểm.
    """
    assert hai_loi_goi["con_lai_tren_dia"] == [0, 0], (
        f"test ĐỂ LẠI dấu vết: {hai_loi_goi['con_lai_tren_dia']} — tool đã tự "
        "commit, `rollback()` không còn đủ. Phải thêm bước dọn theo mã vé "
        f"{hai_loi_goi['ve']} trước khi chạy lại."
    )


@pytest.mark.xfail(
    strict=True,
    reason="FINDING MỞ 17/08 — KHÔNG có chống-trùng ở bất kỳ tầng nào: không "
    "UniqueConstraint trên complaints, create_ticket_with_fraud_check không tra "
    "khiếu nại cũ, TurnGuard chỉ chặn nhánh abandoned. Hai lời gọi ⟹ HAI hồ sơ. "
    "Chờ PO thật chốt: chống-trùng là quy tắc NGHIỆP VỤ, không phải lựa chọn kỹ "
    "thuật. Khi có chống-trùng, test này XANH và xfail(strict) sẽ đỏ — đó là tín "
    "hiệu gỡ dấu, không phải lỗi mới.",
)
def test_hai_loi_goi_trong_mot_luot_chi_sinh_MOT_ho_so(hai_loi_goi):
    """🔴 BẤT BIẾN CHÍNH."""
    d = hai_loi_goi
    assert d["d_complaint"] <= 1 and d["d_ticket"] <= 1, (
        f"hai lời gọi `create_ticket` sinh {d['d_complaint']} complaint · "
        f"{d['d_ticket']} ticket — vé: {d['ve']}\n"
        "Trên đường thật: hai hồ sơ vào hàng chờ CSKH cho MỘT sự việc, khách chỉ "
        "được báo MỘT mã. Vé thứ hai là một khiếu nại không ai nhận."
    )


def test_ca_hai_loi_goi_deu_THANH_CONG_khong_phai_mot_cai_loi(hai_loi_goi):
    """Loại bỏ cách đọc nhẹ nhất — và nó là cách đọc đội đã tin cả buổi.

    Nếu lời gọi thứ hai **lỗi**, thì `Δ=2` ở trên là chuyện khác hẳn: hệ có một
    đường chặn, chỉ là chặn muộn. Test này chứng minh **không phải vậy** — cả
    hai lời gọi đều trả vé, cả hai đều ghi.

    Không có nó, bất biến trên vẫn đỏ nhưng người đọc được phép hy vọng vào một
    cơ chế mà phép đo chưa loại trừ.
    """
    d = hai_loi_goi
    assert d["trang_thai"] == [None, None], (
        f"một lời gọi trả status={d['trang_thai']} — có đường chặn, đọc lại"
    )
    assert all(d["ve"]) and d["ve"][0] != d["ve"][1], (
        f"hai lời gọi không sinh hai vé RIÊNG: {d['ve']}"
    )
