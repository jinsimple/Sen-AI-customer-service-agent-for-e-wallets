"""`la_bi_chan()` (src/cong_ra_ngoai.py) — phân biệt "TA TỰ CHẶN lượt gọi ra
ngoài" với "lỗi THẬT từ nhà cung cấp/mạng". SDK bọc MỌI lỗi transport thành
`openai.APIConnectionError` trước khi tới nơi gọi ⟹ một lượt bị CHÍNH TA
chặn (`GoiRaNgoaiBiChanError`) trông Y HỆT một lượt đứt mạng thật nếu chỉ
nhìn `isinstance(loi, APIConnectionError)`. `la_bi_chan()` lần theo chuỗi
`__cause__`/`__context__` để phân biệt.

Vì sao ca ĐỐI CHỨNG (③) là BẮT BUỘC, không phải phụ: một bản vá kiểu
`isinstance(loi, APIConnectionError) -> tu_chan=True` sẽ làm ca ①② "xanh"
mà SAI HOÀN TOÀN — nó gộp đứt mạng thật vào "ta tự chặn", đúng thứ Luật A
đòi phải bắt được (cổng phải KÊU ở ca nó đáng kêu).

Nguồn đặc tả: Coder (`p-226-32`, 25/08) — công thức bọc lỗi đã được CHÍNH
Coder chạy thật trong container trước khi đưa tôi, không phải tôi tự đoán
từ tên hàm (tester cố ý không đọc `src/`, CLAUDE.md §4). 0 token — không
chạm graph/LLM/DB.
"""
from __future__ import annotations

import httpx
import openai

from src.cong_ra_ngoai import GoiRaNgoaiBiChanError, la_bi_chan


def _boc_nhu_sdk(goc: BaseException) -> openai.APIConnectionError:
    """Mô phỏng ĐÚNG cách SDK nhà cung cấp bọc lỗi transport — công thức xác
    nhận thật bởi Coder (chạy trong container trước khi đưa QA/QC), không
    phải suy diễn từ tên lớp."""
    try:
        raise goc
    except BaseException as e:
        try:
            raise openai.APIConnectionError(request=httpx.Request("POST", "https://x/y")) from e
        except openai.APIConnectionError as boc:
            return boc


def test_ta_tu_chan_bi_boc_boi_sdk_van_nhan_dien_duoc():
    """① Ta tự chặn (GoiRaNgoaiBiChanError), SDK bọc thành APIConnectionError
    — la_bi_chan() phải lần được về nguồn gốc thật qua __cause__."""
    goc = GoiRaNgoaiBiChanError("trần chi tiêu LLM đã chạm, không gọi ra ngoài")
    boc = _boc_nhu_sdk(goc)
    assert isinstance(boc, openai.APIConnectionError), "Ca này phải mô phỏng đúng lớp SDK thật ném ra"
    assert la_bi_chan(boc) is True


def test_doi_chung_dut_mang_that_khong_bi_nhan_nham_thanh_ta_tu_chan():
    """🔴 Ca đối chứng BẮT BUỘC (Luật A) — APIConnectionError THẬT (đứt mạng
    thật), KHÔNG có GoiRaNgoaiBiChanError ở bất kỳ đâu trong chuỗi nguyên
    nhân. Thiếu ca này, cổng không phân biệt được đứt mạng thật với ta tự
    chặn — hai hệ quả xử lý khác hẳn nhau (giữ nguyên `tu_chan=False`)."""
    loi_mang_that = OSError("Network is unreachable")
    boc = _boc_nhu_sdk(loi_mang_that)
    assert la_bi_chan(boc) is False, (
        "la_bi_chan() nhận NHẦM một lỗi mạng thật thành 'ta tự chặn' — sẽ khiến "
        "khách bị đứt mạng thật cũng nhận thông điệp 'liên hệ tổng đài' như thể "
        "ta chủ động chặn, làm sai lệch chẩn đoán vận hành."
    )


def test_loi_nha_cung_cap_thuong_khong_phai_ta_tu_chan():
    """② Lỗi từ nhà cung cấp (vd hết hạn mức bên họ) — không đi qua đường
    bọc APIConnectionError trong ca này (RuntimeError trần, đúng hình dạng
    một lỗi nghiệp vụ NCC không phải lỗi transport) — vẫn phải KHÔNG bị
    nhận diện là 'ta tự chặn'."""
    loi_ncc = RuntimeError("PermissionDeniedError: quota exceeded (nhà cung cấp)")
    assert la_bi_chan(loi_ncc) is False


def test_none_tra_ve_false_khong_nem_loi():
    """Biên đã khai rõ trong chữ ký (`loi: BaseException | None`) — gọi với
    None không được crash, phải trả False (không có gì để lần theo)."""
    assert la_bi_chan(None) is False


def test_ta_tu_chan_bi_boc_nhieu_lop_lien_tiep_van_nhan_dien_duoc():
    """Chuỗi __cause__ dài hơn 1 tầng (vd thư viện trung gian bọc thêm một
    lớp nữa trước khi tới SDK) — vẫn phải lần ra được, miễn trong giới hạn
    `sau_toi_da` mặc định (8)."""
    goc = GoiRaNgoaiBiChanError("chặn ở tầng cong_ra_ngoai")
    boc_lan_1 = _boc_nhu_sdk(goc)
    try:
        raise RuntimeError("một lớp trung gian bọc lại lần nữa") from boc_lan_1
    except RuntimeError as boc_lan_2:
        assert la_bi_chan(boc_lan_2) is True, (
            "la_bi_chan() chỉ lần được ĐÚNG MỘT tầng __cause__ — chuỗi lỗi thật "
            "qua nhiều lớp thư viện trung gian sẽ bị bỏ sót."
        )
