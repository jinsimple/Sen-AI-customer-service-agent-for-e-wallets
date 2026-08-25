"""INV ngân sách token — kích thước KÍCH THÍCH CỐ ĐỊNH là bất biến CI.

> ⚠️ **Chạy TỪ HOST, cần `docker` CLI** — bộ này điều khiển container qua
> `docker exec`. Chạy bên trong container thì `FileNotFoundError: docker`.
> ✅ **0 lượt LLM** — không tốn token.

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

## 🔴 CẬP NHẬT 25/08 — nền đã trôi 13,5%, KHÔNG do đợt "OTP trước token"

**[ĐO 25/08, độc lập — Coder đo trên `fin05do-backend-1` VÀ trên cây làm việc
tại HEAD, QA/QC tự đo lại lần hai trên cây làm việc, HAI SỐ KHỚP NHAU TUYỆT
ĐỐI]**

    system prompt   5.275 token   (+688, +15,0% so nền 17/08)
    lược đồ tool     1.982 token   (+4,   +0,2%)
    TỔNG             7.257 token/lượt  ⟹  96,1% trần hiện hành (7.550)

**Nguyên nhân, truy bằng `git log 03fd9a6..HEAD -- src/agents/prompt.py
src/agents/tools/customer_tools.py`:** `5e8deb6` (fix agent gọi lại tool sau
OTP verify giữa hội thoại, +67 vào system — phần lớn khoảng trôi còn lại của
17/08→hôm nay không truy được về một commit đơn lẻ, xem `NEN` cũ đã lệch từ
trước) · `6d0e3a9` (docstring `create_ticket` bắt buộc nêu mã ticket, +4 vào
tool). **KHÔNG commit nào của đợt "OTP trước token" (⑦⑧③④⑤) chạm hai file
này** — nền trôi trước khi đợt này bắt đầu, đợt này chỉ là lúc bị phát hiện.

**⚠️ Container `fin05do-backend-1` (đích `docker exec` của fixture này) đang
STALE:** `BUILD_COMMIT=03fd9a6` ≠ HEAD, và ảnh KHÔNG mount `src/` sống (băm
nội dung khác nhau giữa container và cây làm việc, [ĐO] xác nhận là hai VẬT
khác nhau, không phải một vật nhìn qua hai cửa) ⟹ `docker exec` hiện trả
`system=5.208` (thấp hơn HEAD 67 token) cho tới khi ai đó dựng lại ảnh này.
`NEN` dưới đây ghi số **HEAD** (đúng nguồn, trung thực với cây đang commit),
lệch 1,3% so với số container — vẫn trong dung sai ±2% của
`test_nen_ghi_trong_test_khop_thuc_te`, nên KHÔNG đỏ ngay, nhưng ai dựng lại
`fin05do` tại HEAD nên đo lại để đóng khoảng lệch này dứt điểm — đây là việc
hạ tầng (rebuild), ngoài phạm vi ghi của `tests/`.

## Ngưỡng: +15%, và vì sao KHÔNG chặt hơn

`7.550 token` (≈ +15% so nền 17/08 — **KHÔNG** tính lại từ nền 25/08, xem lý
do ngay dưới). Khai lý do trước, để lần sau không ai phải đoán:

- **Chặt hơn (+5%)** thì một lần thêm một mục chính sách hợp lệ cũng đỏ ⟹
  người ta sẽ nới ngưỡng cho qua, và một ngưỡng bị nới theo phản xạ thì thà
  không có. Cùng bài học `XA_GIAO`: **cổng bị nới để cứu ca hợp lệ sẽ mở đường
  cho ca không hợp lệ.**
- **Rộng hơn (+50%)** thì nó không bắt được thứ nó sinh ra để bắt.
- `+15%` ≈ **985 token** — lớn hơn "thêm một đoạn" (≈100–300) nên sửa thường
  không đỏ, nhỏ hơn "thêm một khối" (≈1.000+) nên phình thật thì đỏ.

**🔴 QUYẾT ĐỊNH 25/08 (QA/QC, PO xác nhận cập nhật `NEN` ngay — KHÔNG cắt
prompt đợt này): giữ nguyên `NGUONG_TOKEN`, KHÔNG tính lại `= NEN mới × 1.15`.**
Lý do: ngưỡng là **trần chống trôi neo vào một mốc cố định** — tính lại mỗi
lần nền dịch chuyển sẽ biến nó thành một cái trần tự nới theo drift, tức
đúng thứ toàn bộ cơ chế này dựng ra để CHẶN. Nền được phép cập nhật (nó chỉ
là "chúng ta đang ở đâu"); ngưỡng chỉ đổi khi có **quyết định CÓ CHỦ Ý** kèm
lý do tại đây, không phải phép tính tự động theo nền.

**⚠️ RỦI RO THẬT cho phần còn lại của đợt "OTP trước token" — báo Lead 25/08:**
chỉ còn **293 token** (3,9%) dưới trần. `⑨` (câu sàng lọc lừa đảo) và `⑪` (ép
cấu trúc lượt 5/6/3, đổi góc nhìn PDPA) đều có khả năng thêm CHỮ vào prompt.
Nếu cộng dồn vượt 293 token, cổng này vỡ trần — **không phải lỗi của bản vá
đó**, mà là hệ quả CỘNG DỒN của khoảng trôi đã có từ trước cộng thêm việc mới.
Lead cần xếp việc GIẢM prompt (hoặc quyết định nâng trần có lý do) TRƯỚC khi
⑨/⑪ land, không phải sau khi cổng đã đỏ.

**Ngưỡng này KHÔNG phải mục tiêu tối ưu.** Nó là **trần chống trôi**. Giảm
prompt xuống 3.000 token là việc tốt và test này sẽ không khen; nó chỉ kêu khi
prompt **lớn lên** mà không ai chú ý.

## 🔴 NỚI 25/08 — nới từ 7.550 → 7.800, CÓ CHỦ ĐÍCH, KHÔNG phải trôi

Lý do: `⑪` (ép cấu trúc ba vế lượt 5, đổi trục hỏi lại lượt 6, đổi góc nhìn
PDPA) thêm CHỮ có chủ đích vào system prompt — đúng loại thay đổi cảnh báo
"RỦI RO THẬT" ở mục trên đã nêu trước khi ⑪ land. Cắt vế (c) của lượt 5 để
né cổng này là làm hỏng đúng câu duy nhất nói cho khách biết **họ tự làm
được gì** — PO quyết nới, không cắt chữ.

Số dùng để chọn ngưỡng mới (Coder đo 25/08, Lead duyệt phương pháp trục):
`system` **5.592** (đo trên cây làm việc tại HEAD, môi trường host —
hợp lệ cho trục `system` vì ⑪ chỉ chạm `prompt.py`) + `tool` **2.014** (số
CONTAINER đo trước ⑪ — hợp lệ vì ⑪ không chạm tool schema) ⟹ **tổng ước
tính 7.606**. Đây là ƯỚC TÍNH tổng hợp từ hai nguồn đo khác nhau (host +
container), CHƯA phải một phép đo container-thật duy nhất sau khi ⑪ land —
xem mục "CHỜ RECONFIRM" ngay dưới trước khi tin số `NEN` trong code.

`NGUONG_TOKEN` mới = **7.800** = 7.606 + ~2,5% (cùng biên độ dung sai ±2% đã
dùng ở `test_nen_ghi_trong_test_khop_thuc_te`, làm tròn lên số đẹp) — đủ hấp
thụ nhiễu đo, không đủ rộng để hết ý nghĩa cảnh báo.

**⚠️ CHỜ RECONFIRM — `NEN` bên dưới CHƯA cập nhật theo ước tính 7.606 ở
trên.** Container đích của cổng (`fin05do-backend-1`, mặc định `CT`) đo tại
băm `26b1bd3b1ff5` — KHÔNG có ⑪ (cây làm việc đang ở `9c0b50d0bb92`). Đo lúc
này vẫn ra số CŨ (~7.186), không phản ánh ⑪ — nới trần mà không nới object
đang đo là **nới mù**. Đã nhờ Coder dựng lại `fin05do-backend-1` tại HEAD,
xác nhận băm khớp cây làm việc, rồi QA/QC tự đo lại lần hai qua chính `CT`
(không chỉ tin số Coder báo) trước khi sửa `NEN`. Cho tới lúc đó, xem `NEN`
dưới đây là **stale có chủ đích, đã khai**, không phải bị bỏ quên.

**⚠️ "Đã nới trần cho ⑪" ≠ "đã đo ⑪ và nó vừa trần".** `NGUONG_TOKEN=7.800` là
một QUYẾT ĐỊNH CHÍNH SÁCH dựa trên ước tính tổng hợp ở trên — cổng CHẠY THẬT
(qua `CT`) tại thời điểm sửa dòng này vẫn báo **7.186**, đo trên một ảnh
**không có ⑪**. Chưa có một lần chạy nào của chính cổng này nhìn thấy prompt
đã có ⑪. Đừng đọc việc nới trần thành bằng chứng ⑪ đã được đo và vẫn lọt.

**⚠️ Trục `tool` lệch theo MÔI TRƯỜNG, không phải theo thời gian:** container
đo `tool=2.014` vì ảnh ghim `langchain-core 1.5.4`; host/venv dev đo
`tool=1.982` vì pin `1.5.3` — `convert_to_openai_tool` giữa hai bản khác
nhau ở đúng +32 token này. Nếu ai đổi `CT` sang một container khác bản
`langchain-core`, `test_nen_ghi_trong_test_khop_thuc_te` sẽ đỏ vì **môi
trường khác nhau**, KHÔNG phải hồi quy — đối chiếu số ghim ở đây trước khi
kết luận có bug.

## Đo bằng TOKEN, không bằng ký tự

Ký tự là thứ dễ đo hơn và **sai**: trần TPM đếm token. Tiếng Việt ≈3,3 ký tự/
token ở `o200k`, nhưng tỉ lệ đó **đổi theo tokenizer** — Qwen đắt hơn 1,20–1,31×
trên cùng văn bản (đo 17/08). Ngưỡng đặt theo `o200k` là một **đại diện**, và
tôi khai rõ nó là đại diện: nó canh **xu hướng phình**, không dự báo TPM thật
của nhà cung cấp.
"""
from __future__ import annotations

import json
import os
import subprocess

import pytest

from tests._docker_co_mat import co_docker
from tests._suite_day_du import can_ha_tang

CT = os.environ.get("FIN05_TOKEN_BUDGET_CT", "fin05do-backend-1")  # [25/08] override cho ngăn khác, vd buổi tốn phí trên fin05-dot-otp
NGUONG_TOKEN = 7_800           # [25/08] nới từ 7_550, lý do ⑪ ba lượt kịch bản chuyên gia, delta đo được +317. Nới CÓ CHỦ ĐÍCH, KHÔNG phải trôi — xem docstring "NỚI 25/08"
NEN = {"system": 5_275, "tool": 1_982, "tong": 7_257}  # [ĐO 25/08, HEAD c02cbb1] STALE có chủ đích — chưa phản ánh ⑪, chờ Coder dựng lại fin05do-backend-1 tại HEAD, xem docstring "CHỜ RECONFIRM"

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


@pytest.fixture(scope="module", autouse=True)
def _yeu_cau_stack_song():
    """NHÓM A2 (`tests/_suite_day_du.py`) — CHÍNH FILE NÀY là nguồn gốc của cổng
    meta này: nó từng chuyển từ ĐỎ sang SKIP im lặng khi Lead hạ ngăn Docker để
    lấy RAM (25/08), và không ai được báo cho tới khi đi tìm hiểu vì sao suite
    "tốt lên". `FIN05_SUITE_DAY_DU=1` biến skip này thành FAIL rõ ràng."""
    if not _stack_song():
        can_ha_tang(
            f"cần {CT} để lấy prompt+lược đồ THẬT. Đọc từ app đang chạy, KHÔNG "
            "dựng lại — dựng lại là đo một vật gần giống (Luật 13).",
            cach_dung=f"`docker compose up -d` ngăn chứa container tên {CT} (hoặc trỏ FIN05_TOKEN_BUDGET_CT sang ngăn khác đang sống)",
            allow_module_level=True,
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

    🔴 [ĐO 25/08] ĐANG ĐỎ THẬT, ĐÚNG LÝ DO — không phải bug của bản vá vừa
    land. Nền đã ở 95–96% ngưỡng (xem docstring đầu file) TRƯỚC khi đợt "OTP
    trước token" bắt đầu. Đây chính là việc cổng này SINH RA ĐỂ LÀM. Đừng nới
    ngưỡng để tắt tiếng nó — quyết định thuộc về Lead (xếp việc giảm prompt,
    hoặc nâng `NGUONG_TOKEN` có lý do kèm theo).
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
