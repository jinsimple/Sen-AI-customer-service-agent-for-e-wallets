"""Canh hai bản vá bộ đo ngày 15/08 — backoff 429, và "0 lượt thì không TRƯỢT".

Cả hai bản vá ra đời từ cùng một đêm đo, và cả hai đều thuộc loại nguy hiểm
nhất: chúng làm con số ĐẸP LÊN. Backoff làm bớt ca hỏng; luật-0-lượt làm bớt
ca trượt. Một bản vá làm đẹp số liệu mà không có ca canh vế ngược thì không
phân biệt được với việc nới lỏng bộ đo cho dễ nhìn.

Nên mỗi bản vá ở đây đều có ĐỦ HAI VẾ:
  · Luật 1 — nó có THẬT SỰ hoạt động không? (thử lại thật, xếp lại trạng thái thật)
  · Luật 2 — nó có QUÁ RỘNG không? (lỗi thường KHÔNG được thử lại, ca có
    lượt chạy vẫn TRƯỢT như thường)

Vế thứ hai mới là vế đáng viết. Một `goi_agent_thu_lai` nuốt mọi exception rồi
thử lại 4 lần sẽ làm suite xanh ở mọi test của vế thứ nhất, đồng thời biến mọi
lỗi sản phẩm thật thành "chờ rồi thử lại" — tức bộ đo mù hẳn một loại lỗi.
"""
from __future__ import annotations

import time

import pytest

from tests._eval_co_mat import doi_hoi_eval

# Thiếu `eval/` ⟹ SKIP cả module KÈM LÝ DO (tests/_eval_co_mat.py).
# Trong container `.dockerignore` loại eval/ CÓ CHỦ ĐÍCH — heldout_set
# là tập NIÊM PHONG, không được vào ảnh. Thiếu nó KHÔNG phải lỗi tệp test.
doi_hoi_eval()

from eval._harness import (
    _CHO_TOI_DA_GIAY,
    _SO_LAN_THU_LAI,
    _cho_bao_lau,
    goi_agent_thu_lai,
    xep_trang_thai,
)


class RateLimitError(Exception):
    """Giả lỗi 429 của OpenAI. Tên lớp quan trọng: `_cho_bao_lau` nhận diện
    qua `repr()`, đúng như lỗi thật xuất hiện trong bản ghi."""


# ─────────────────────────── Luật 1 — có hoạt động không ───────────────────

@pytest.mark.parametrize(
    "thong_diep,cho_ky_vong",
    [
        # Hai chuỗi này CHÉP NGUYÊN VĂN từ traceback thật của MT-A01/MT-F01
        # ngày 15/08 — không phải ví dụ tôi tự nghĩ ra. Đó là lý do test này
        # có giá trị: nó khớp với định dạng OpenAI THẬT SỰ trả về.
        ("Rate limit reached ... Please try again in 2.793s. Visit ...", 2.793 + 0.5),
        ("Rate limit reached ... Please try again in 300ms. Visit ...", 0.3 + 0.5),
    ],
)
def test_doc_dung_khoang_cho_openai_tu_noi(thong_diep: str, cho_ky_vong: float):
    assert _cho_bao_lau(RateLimitError(thong_diep)) == pytest.approx(cho_ky_vong, abs=0.01)


def test_429_khong_noi_ro_thi_van_cho_mot_khoang_an_toan():
    """Không parse được ≠ bỏ cuộc. Vẫn là 429, vẫn đáng thử lại."""
    assert _cho_bao_lau(RateLimitError("Error code: 429 - rate limit exceeded")) == 5.0


def test_khong_cho_lau_hon_tran():
    """Chặn trên: một lỗi báo 'try again in 3600s' không được làm treo lượt đo."""
    assert _cho_bao_lau(RateLimitError("try again in 3600s")) == _CHO_TOI_DA_GIAY


def test_thu_lai_that_va_tra_ve_ket_qua_khi_thanh_cong(monkeypatch):
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    lan = {"n": 0}

    def ham():
        lan["n"] += 1
        if lan["n"] < 3:
            raise RateLimitError("Please try again in 300ms")
        return {"reply": "xong"}

    assert goi_agent_thu_lai(ham) == {"reply": "xong"}
    assert lan["n"] == 3, "phải gọi lại đúng số lần cần thiết, không nhiều không ít"


def test_het_luot_thu_thi_nem_lai_chu_khong_nuot(monkeypatch):
    """Thử lại là để ĐO ĐƯỢC, không phải để GIẤU.

    Nếu hết lượt mà nuốt lỗi rồi trả về None, case sẽ chạy tiếp với dữ liệu
    rỗng và bị chấm TRƯỢT — biến một lần hết-hạn-mức thành một kết luận sai
    về agent. Phải ném lại để `phan_loai_loi` xếp KHÔNG ĐO ĐƯỢC.
    """
    monkeypatch.setattr(time, "sleep", lambda _s: None)
    lan = {"n": 0}

    def ham_luon_429():
        lan["n"] += 1
        raise RateLimitError("Please try again in 300ms")

    with pytest.raises(RateLimitError):
        goi_agent_thu_lai(ham_luon_429)
    assert lan["n"] == _SO_LAN_THU_LAI


# ─────────────────────────── Luật 2 — có quá rộng không ────────────────────

@pytest.mark.parametrize(
    "loi",
    [
        ValueError("agent trả về payload sai định dạng"),
        KeyError("trans_id"),
        # Lỗi THẬT của MT-F01. Đây là ca quan trọng nhất khối này: nó là lỗi
        # đã làm tôi phải viết bản vá kia, nên rất dễ bị gộp nhầm vào đây cho
        # "gọn". Gộp vào thì mỗi lần FK gãy, bộ đo sẽ chờ rồi thử lại 4 lần và
        # hỏng y hệt — chỉ chậm hơn gấp bốn và khó thấy hơn nhiều.
        Exception("(sqlite3.IntegrityError) FOREIGN KEY constraint failed"),
    ],
    ids=["ValueError", "KeyError", "IntegrityError_that_cua_MT-F01"],
)
def test_loi_thuong_khong_duoc_thu_lai(loi: Exception, monkeypatch):
    """Vế sống còn: chỉ 429 mới được thử lại.

    Thiếu test này thì một `except Exception: retry` sẽ xanh hết mọi test phía
    trên, đồng thời nuốt mọi lỗi sản phẩm thật thành độ trễ.
    """
    monkeypatch.setattr(time, "sleep", lambda _s: pytest.fail("KHÔNG được chờ với lỗi thường"))
    lan = {"n": 0}

    def ham():
        lan["n"] += 1
        raise loi

    with pytest.raises(type(loi)):
        goi_agent_thu_lai(ham)
    assert lan["n"] == 1, f"{type(loi).__name__} bị thử lại {lan['n']} lần — chỉ 429 mới được thử lại"


def test_khong_phai_429_thi_khong_tra_ve_khoang_cho():
    assert _cho_bao_lau(ValueError("lỗi thường")) is None
    assert _cho_bao_lau(Exception("FOREIGN KEY constraint failed")) is None


# ────────────── Luật-0-lượt: canh trên chính BẢN GHI đã lưu ────────────────

@pytest.mark.parametrize(
    "ha_tang,so_luot,vi_pham,ky_vong",
    [
        # 0 lượt + KHÔNG dấu hiệu hạ tầng -> phạm trù riêng. Đây là ca MT-F01.
        (None, 0, ["LỖI CHẠY CASE: IntegrityError(...)"], "chua_co_hanh_vi"),
        # 0 lượt NHƯNG là 429 -> vẫn là hạ tầng, vì hành động cần làm khác hẳn:
        # chạy lại thì xong, không có gì để điều tra. Đây là ca MT-A01.
        ("LỖI HẠ TẦNG (không đo được): RateLimitError(...)", 0, [], "khong_do_duoc"),
        # CÓ hành vi + CÓ vi phạm -> vẫn TRƯỢT như thường. Vế Luật 2 của
        # luật-0-lượt: thiếu ca này thì một bản vá quét sạch mọi TRƯỢT thành
        # "chưa có hành vi" vẫn xanh hết, và bộ đo không bao giờ báo đỏ nữa.
        (None, 3, ["lượt 2: hứa hoàn tiền"], "truot"),
        (None, 5, [], "dat"),
    ],
    ids=["0luot_loi_la->chua_co_hanh_vi", "0luot_429->khong_do_duoc",
         "co_luot_co_vi_pham->TRUOT", "co_luot_sach->DAT"],
)
def test_xep_trang_thai_du_bon_nhanh(ha_tang, so_luot, vi_pham, ky_vong):
    """Bốn nhánh gán trạng thái, gọi thẳng vào hàm.

    Lỗi 15/08 sống sót được vì phép gán này từng là một biểu thức ba ngôi kẹp
    giữa vòng lặp `run()` — không test nào gọi tới được. Tách ra hàm thuần là
    một phần của bản vá, không phải dọn dẹp cho đẹp: **một nhánh quyết định
    không gọi được từ test là một nhánh không ai canh.**
    """
    assert xep_trang_thai(
        ha_tang=ha_tang, so_luot_chay_xong=so_luot, vi_pham=vi_pham
    ) == ky_vong


def test_khong_ban_ghi_moi_nao_truot_voi_khong_luot_nao_chay(ban_ghi_adversarial):
    """Chốt chặn trên ARTIFACT — canh bản ghi do THƯỚC HIỆN TẠI sinh ra.

    Chỉ soi bản ghi mang dấu thước hiện hành: bản ghi cũ mang nhãn cũ là đúng
    lịch sử, không phải lỗi cần sửa — viết lại nhãn của chúng mới là làm hỏng
    sổ. Đây là chỗ test này khác `test_xep_trang_thai_du_bon_nhanh`: hàm kia
    canh LOGIC, hàm này canh việc logic ấy có thật sự được DÙNG trong đường
    chạy thật hay không.
    """
    from eval.measure_quality import dau_thuoc

    thuoc_nay = dau_thuoc()["cham_diem"]
    moi = [r for r in ban_ghi_adversarial if r.get("_thuoc", {}).get("cham_diem") == thuoc_nay]
    if not moi:
        pytest.skip(f"Chưa có bản ghi nào sinh bởi thước hiện tại ({thuoc_nay}) — chưa đo được.")
    xau = [
        (r["_ten_file"], r["case_id"])
        for r in moi
        if r.get("trang_thai") == "truot" and not (r.get("all_agent_replies") or [])
    ]
    assert not xau, (
        "Bản ghi TRƯỢT nhưng 0 lượt chạy xong — bộ đo đang phán về hành vi nó "
        f"chưa quan sát được: {xau}"
    )
