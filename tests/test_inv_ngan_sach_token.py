"""INV ngân sách token — kích thước KÍCH THÍCH CỐ ĐỊNH là bất biến CI.

    system prompt + lược đồ tool  ≤ NGƯỠNG   (đo bằng token, không bằng ký tự)

## Vì sao đây là bất biến, không phải một con số theo dõi

Chuyên gia tối ưu token nêu, và nó đúng văn hoá dự án này: *"prompt phình 500
token vì ai đó thêm một đoạn là **drift im lặng** — không ai thấy cho tới khi
thông lượng tụt."*

Đây là **kích thích CỐ ĐỊNH**: nó đi kèm **mọi** lượt đầy đủ, bất kể khách hỏi
gì. Nên một dòng thêm vào prompt nhân lên theo **số lượt của cả hệ**, và với ta
thứ chặn đích 100 CSKH là **trần TPM**, không phải tiền.

> Một hằng số người-phải-nhớ-cập-nhật thì sẽ hỏng im lặng — cùng họ
> `DAI_TOI_DA`, `_CHARS_TOOL_SCHEMA`, `CONTRACT_VERSION`. Khác biệt duy nhất là
> cái này **đo được bằng máy**, nên nó không cần ai nhớ.

## Số nền, đo 17/08 (`tiktoken o200k_base`)

    system prompt   15.094 ký tự · 4.587 token
    lược đồ tool     6.773 ký tự · 1.978 token
    TỔNG                           6.565 token/lượt

## Ngưỡng: +15%, và vì sao KHÔNG chặt hơn

`7.550 token` (≈ +15%). Khai lý do trước, để lần sau không ai phải đoán:

- **Chặt hơn (+5%)** thì một lần thêm một mục chính sách hợp lệ cũng đỏ ⟹
  người ta sẽ nới ngưỡng cho qua, và một ngưỡng bị nới theo phản xạ thì thà
  không có. Cùng bài học `XA_GIAO`: **cổng bị nới để cứu ca hợp lệ sẽ mở đường
  cho ca không hợp lệ.**
- **Rộng hơn (+50%)** thì nó không bắt được thứ nó sinh ra để bắt.
- `+15%` ≈ **985 token** — lớn hơn "thêm một đoạn" (≈100–300) nên sửa thường
  không đỏ, nhỏ hơn "thêm một khối" (≈1.000+) nên phình thật thì đỏ.

**Ngưỡng này KHÔNG phải mục tiêu tối ưu.** Nó là **trần chống trôi**. Giảm
prompt xuống 3.000 token là việc tốt và test này sẽ không khen; nó chỉ kêu khi
prompt **lớn lên** mà không ai chú ý.

## Đo bằng TOKEN, không bằng ký tự

Ký tự là thứ dễ đo hơn và **sai**: trần TPM đếm token. Tiếng Việt ≈3,3 ký tự/
token ở `o200k`, nhưng tỉ lệ đó **đổi theo tokenizer** — Qwen đắt hơn 1,20–1,31×
trên cùng văn bản (đo 17/08). Ngưỡng đặt theo `o200k` là một **đại diện**, và
tôi khai rõ nó là đại diện: nó canh **xu hướng phình**, không dự báo TPM thật
của nhà cung cấp.
"""
from __future__ import annotations

import json
import subprocess

import pytest

CT = "fin05do-backend-1"
NGUONG_TOKEN = 7_550          # nền 6.565 + ~15%
NEN = {"system": 4_587, "tool": 1_978, "tong": 6_565}

_MA = r'''
import datetime as dt, json
from src.agents.prompt import build_system_prompt as B
from src.agents.tools.customer_tools import build_customer_tools as T
from langchain_core.utils.function_calling import convert_to_openai_tool as C
class S:
    def __getattr__(self, n): return None
sp = B(current_time=dt.datetime(2026, 8, 17, 10, 0, 0), customer_name="Nguyễn Văn A")
tj = json.dumps([C(t) for t in T(S(), user_id="u")], ensure_ascii=False)
print(json.dumps({"sys": sp, "tool": tj}, ensure_ascii=False))
'''


def _stack_song() -> bool:
    r = subprocess.run(["docker", "ps", "-q", "-f", f"name={CT}"],
                       capture_output=True, text=True)
    return bool(r.stdout.strip())


pytestmark = pytest.mark.skipif(
    not _stack_song(),
    reason=f"cần {CT} để lấy prompt+lược đồ THẬT. Đọc từ app đang chạy, KHÔNG "
           "dựng lại — dựng lại là đo một vật gần giống (Luật 13).",
)


@pytest.fixture(scope="module")
def kich_thich() -> dict[str, int]:
    tiktoken = pytest.importorskip(
        "tiktoken",
        reason="thiếu NĂNG LỰC thật: không có tiktoken thì không đếm token được. "
               "KHÔNG thay bằng đếm ký tự — ký tự là một đại lượng KHÁC, và thay "
               "thầm lặng là đổi vật đo (Luật 13).",
    )
    r = subprocess.run(["docker", "exec", CT, "python", "-c", _MA],
                       capture_output=True, text=True, timeout=180)
    assert r.returncode == 0, f"không lấy được kích thích: {(r.stderr or r.stdout)[-300:]}"
    d = json.loads(r.stdout.strip().splitlines()[-1])
    e = tiktoken.get_encoding("o200k_base")
    return {"system": len(e.encode(d["sys"])), "tool": len(e.encode(d["tool"]))}


def test_kich_thich_co_dinh_khong_vuot_ngan_sach(kich_thich, capsys):
    """🔴 BẤT BIẾN: system prompt + lược đồ tool ≤ 7.550 token.

    IN CHỖ TRỐNG CÒN LẠI mỗi lần chạy, không chỉ xanh/đỏ. Một cổng chỉ có hai
    trạng thái giấu mất **xu hướng**: prompt bò từ 6.565 lên 7.400 qua mười lần
    sửa vẫn xanh cả mười lần, rồi đỏ ở lần mười một — và lúc đó không ai biết
    nó đã bò từ bao giờ.

    Con số này in ra cả khi ĐẠT (`-s` để thấy), nên nó thành một chuỗi thời
    gian đọc được từ log CI thay vì một bit.
    """
    tong = kich_thich["system"] + kich_thich["tool"]
    con = NGUONG_TOKEN - tong
    with capsys.disabled():
        print(
            f"\n  NGÂN SÁCH TOKEN  {tong:,}/{NGUONG_TOKEN:,}"
            f"  ·  còn {con:,} ({con / NGUONG_TOKEN:.0%})"
            f"  ·  so nền {tong - NEN['tong']:+,}"
            f"\n    system {kich_thich['system']:,} ({kich_thich['system'] - NEN['system']:+,})"
            f"  ·  tool {kich_thich['tool']:,} ({kich_thich['tool'] - NEN['tool']:+,})"
        )
    assert tong <= NGUONG_TOKEN, (
        f"kích thích cố định = {tong:,} token > ngưỡng {NGUONG_TOKEN:,}\n"
        f"  system {kich_thich['system']:,} (nền {NEN['system']:,}) · "
        f"tool {kich_thich['tool']:,} (nền {NEN['tool']:,})\n"
        "Con số này đi kèm MỌI lượt đầy đủ ⟹ nó nhân lên theo số lượt của cả hệ,\n"
        "và thứ chặn đích 100 CSKH là TRẦN TPM, không phải tiền.\n"
        "Nếu phình là CỐ Ý: sửa NGUONG_TOKEN kèm lý do, đừng nới im lặng."
    )


def test_bao_TRUOC_khi_cham_tran(kich_thich):
    """Kêu ở 90% ngưỡng — để cú vượt không đến bất ngờ giữa một đợt đo.

    Một cổng chỉ có hai trạng thái xanh/đỏ sẽ đỏ đúng lúc tệ nhất: khi ai đó
    vừa land xong và đang chờ chạy đo. Cảnh báo sớm cho người sửa một cửa sổ để
    chọn — cắt bớt, hay nâng ngưỡng có lý do.
    """
    tong = kich_thich["system"] + kich_thich["tool"]
    canh = int(NGUONG_TOKEN * 0.9)
    if tong > canh:
        pytest.fail(
            f"⚠️ {tong:,} token đã vượt 90% ngưỡng ({canh:,}/{NGUONG_TOKEN:,}). "
            "Chưa vỡ ngân sách, nhưng chỗ trống còn lại không đủ cho một khối mới."
        )


def test_nen_ghi_trong_test_khop_thuc_te(kich_thich):
    """Số NỀN trong file này phải đúng với thực tế — nếu không, mọi lý lẽ về
    biên độ ±15% ở docstring nói về một vật khác.

    Cho phép lệch ±2% : `current_time` đi vào prompt nên độ dài dao động nhẹ
    theo ngày/giờ (phát hiện 17/08). Lệch hơn thế là prompt đã đổi thật, và
    docstring cần cập nhật cùng lúc với ngưỡng.
    """
    for ten in ("system", "tool"):
        lech = abs(kich_thich[ten] - NEN[ten]) / NEN[ten]
        assert lech <= 0.02, (
            f"nền `{ten}` ghi {NEN[ten]:,}, thực tế {kich_thich[ten]:,} "
            f"(lệch {lech:.1%}). Cập nhật NEN và lý lẽ biên độ trong docstring."
        )
