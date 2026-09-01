"""② hạng mục PO giao 26/08, sau lỗ `41aacd5`: 10 ngày (16-26/08)
golden_set/adversarial_set chấm nhầm qua `gpt-4o-mini` (OpenAI thật) vì
LLM_BASE_URL/LLM_MODEL/LLM_API_KEY rỗng CÙNG HƯỚNG, gọi thật THÀNH CÔNG,
không một dòng lỗi — và không file kết quả nào từng ghi model đã dùng.

PO: "đừng chỉ ghi rồi trông chờ người đọc để ý... 'tra được' ≠ 'kêu'." Nên
đây không phải test "trường có tồn tại" mà test GATE: sai nguồn phải làm
báo cáo TỰ XƯNG "KHÔNG DÙNG ĐƯỢC" ngay dòng đầu — và ca ĐÚNG nguồn (đối
chứng bắt buộc, Luật A) phải im lặng, không được kêu oan.

0 token — không gọi LLM/graph/DB thật. `write_report()` là hàm định dạng
thuần (nhận list[dict] đã có sẵn, ghi file), không có gì trong đường đo này
chạm mạng.
"""
from __future__ import annotations

import pytest

from tests._eval_co_mat import doi_hoi_eval

doi_hoi_eval()

from eval._harness import (  # noqa: E402 — CỐ Ý sau doi_hoi_eval()
    MODEL_GHIM_MAC_DINH,
    dong_bang_nguon_mo_hinh,
    xac_nhan_nguon_mo_hinh_luc_chay,
)
from eval.run_adversarial_set import write_report as write_report_adv  # noqa: E402
from eval.run_golden_set import write_report as write_report_golden  # noqa: E402


def test_dung_duoc_khi_model_khop_va_base_url_co(monkeypatch):
    """Ca ĐỐI CHỨNG BẮT BUỘC (Luật A) — nguồn ĐÚNG phải im lặng, không kêu
    oan. Thiếu ca này, một bản vá kiểu "luôn luôn KHÔNG DÙNG ĐƯỢC" cũng làm
    2 ca âm tính dưới đây xanh y hệt."""
    monkeypatch.setenv("LLM_MODEL", MODEL_GHIM_MAC_DINH)
    monkeypatch.setenv("LLM_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert info["dung_duoc"] is True
    banner = dong_bang_nguon_mo_hinh(info)
    assert "KHÔNG DÙNG ĐƯỢC" not in banner
    assert banner.startswith("✅")


def test_khong_dung_duoc_khi_model_lech_ghim(monkeypatch):
    """Đúng lỗ 41aacd5 phần MODEL: base_url có đặt, nhưng model đọc được
    không phải model ghim của dự án (vd rơi về gpt-4o-mini)."""
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert info["dung_duoc"] is False
    banner = dong_bang_nguon_mo_hinh(info)
    assert "KHÔNG DÙNG ĐƯỢC" in banner
    assert "gpt-4o-mini" in banner


def test_khong_dung_duoc_khi_base_url_rong(monkeypatch):
    """Đúng lỗ 41aacd5 phần BASE_URL: model đọc được khớp ghim, nhưng
    base_url rỗng — vẫn KHÔNG suy được đích THẬT đã gọi tới (SDK có thể đã
    rơi mặc định OpenAI thật ngay cả khi biến LLM_MODEL đọc ra đúng)."""
    monkeypatch.setenv("LLM_MODEL", MODEL_GHIM_MAC_DINH)
    monkeypatch.setenv("LLM_BASE_URL", "")
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert info["dung_duoc"] is False
    banner = dong_bang_nguon_mo_hinh(info)
    assert "KHÔNG DÙNG ĐƯỢC" in banner
    assert "base_url RỖNG" in banner


def test_doc_truc_tiep_os_environ_ca_bien_chua_dat(monkeypatch):
    """Ba trạng thái (memory dự án: unset ≠ rỗng ≠ có giá trị) — biến CHƯA
    ĐẶT (None) không được nhầm thành 'trùng ghim' hay crash. `delenv` thay vì
    `setenv(..., "")` để đúng trạng thái 'chưa đặt', không phải 'đặt rỗng'."""
    monkeypatch.delenv("LLM_MODEL", raising=False)
    monkeypatch.delenv("LLM_BASE_URL", raising=False)
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert info["model"] is None
    assert info["base_url"] is None
    assert info["dung_duoc"] is False


def test_bam_ma_nguon_co_mat_va_la_chuoi_khong_rong(monkeypatch):
    """Trường thứ ba PO yêu cầu (`bam_ma_nguon`) — không chỉ model/base_url."""
    monkeypatch.setenv("LLM_MODEL", MODEL_GHIM_MAC_DINH)
    monkeypatch.setenv("LLM_BASE_URL", "https://x")
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert isinstance(info["bam_ma_nguon"], str) and len(info["bam_ma_nguon"]) > 0


@pytest.mark.parametrize("write_report", [write_report_golden, write_report_adv])
def test_banner_kem_theo_o_dau_bao_cao_khong_bi_chon_vui(write_report, tmp_path, monkeypatch):
    """🔴 Ca GATE chính — dòng tự khai phải nằm ở ĐẦU báo cáo (trong 5 dòng
    đầu), không phải một ghi chú lặng lẽ cuối file mà người đọc lướt sẽ bỏ
    qua. Test cả `run_golden_set.write_report` lẫn `run_adversarial_set.
    write_report` — hai hàm định dạng độc lập, một bản vá chỉ vá một bên sẽ
    bị bên kia bắt được."""
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_BASE_URL", "")
    info = xac_nhan_nguon_mo_hinh_luc_chay()
    assert info["dung_duoc"] is False  # tiền đề của ca này

    out_path = tmp_path / "report.md"
    # `results=[]` — 0 case, đủ để kiểm banner mà không cần chạy agent thật.
    write_report([], out_path, info)
    noi_dung = out_path.read_text(encoding="utf-8")
    dau_bao_cao = "\n".join(noi_dung.splitlines()[:5])
    assert "KHÔNG DÙNG ĐƯỢC" in dau_bao_cao, (
        f"Banner tự khai không nằm trong 5 dòng đầu báo cáo — dễ bị người đọc "
        f"lướt bỏ qua. 5 dòng đầu thật:\n{dau_bao_cao}"
    )
