"""Cổng ký cho mọi bản vá chạm mẫu tier-1 TIẾNG ANH — corpus đủ trục (41 ca).

Nguồn: `docs/security/corpus-doi-chung-EN-du-truc.jsonl` (+ `.md` giải thích),
security giao 15/08 (`b92b24c`). **Thay** bộ 7 câu đối chứng cũ ở `F-28 §2`.

## Vì sao bộ 7 câu cũ phải bị thay — dạng lỗi đáng nhớ hơn cả bản vá

Bộ cũ **không thiếu một cách chung chung**. Nó **ĐỦ cho bản vá TRƯỚC và HỤT
cho bản vá SAU**:

| Bản vá | Trục nó chạm | Bộ 7 câu phủ? |
|---|---|---|
| F-28 — mở họ **ĐỘNG TỪ** | từ vựng động từ | ✅ ký ĐẠT hợp lệ |
| F-28b — mở **HÌNH THÁI** (`\\w*`) | hình thái · phủ định · thân từ | ❌ ký sẽ SAI |

⟹ **Luật 8 áp cho CÔNG CỤ ĐO thay vì cho quyết định**: mỗi lần đổi/mở rộng một
mẫu, hỏi lại *"bộ đối chứng có còn phủ trục MỚI không"* — không tái dùng chỉ vì
"lần trước nó chạy". Một corpus hợp lệ hôm qua có thể thành cổng rỗng hôm nay
mà không đổi một ký tự nào.

Và một lỗ **cấu trúc** cả ba vai cùng trượt: `FP 0/2006` đo trên kho MoMo —
**2.006 câu đó là TIẾNG VIỆT**, nên về cấu trúc nó **không thể** bắt FP của một
mẫu tiếng Anh. Số đúng, nhưng **không nói gì** về lớp đang xét. *Corpus đối
chứng phải CÙNG NGÔN NGỮ với mẫu đang đo* — hiển nhiên khi viết ra, và cả ba
chúng tôi đều trượt.

## BA mức kỳ vọng, không phải hai — điểm bộ cũ không diễn đạt được

    phai_bat         (16)  tier1 HOẶC tier2 đều ĐẠT
    khong_xoa_trang  (18)  CẤM tier1 · tier2 CHẤP NHẬN ĐƯỢC
    sach             ( 7)  nên ra ""

Corpus lớn dần theo trục, KHÔNG cố định: ba vai đã thêm ba trục khác nhau
(security hình-thái + phủ-định · tester `disregarding` · tech-lead danh-từ-đích).
Trục 6 `danh_tu_dich_hop_le` (EN-D01..08) làm ĐỔ cả 8 động từ tier-1 EN — và nó
khác cả hai trục thêm trước đó. Đó là dữ kiện, không phải sự cố: **một bộ đối
chứng do MỘT vai soạn gần như chắc chắn hụt trục của vai khác**, không vì ai cẩu
thả mà vì mỗi vai nhìn từ một phía.

Mức giữa là mức bộ cũ **không có**. Sau khi mẫu mở rộng chuyển xuống tier-2,
một khuyến cáo an toàn bị **gắn nhãn** tier-2 là chấp nhận được — nội dung vẫn
tới khách, chỉ **xoá trắng** mới là hỏng (F-25 §4: *"nếu tier-2 đánh dấu thì
đạt"*). Bộ cũ chỉ có `""` nên sẽ **báo đỏ nhầm cho một hành vi đúng** — tức tự
biến thành cổng-đỏ-vì-lý-do-sai, thứ dạy cả đội bỏ qua nó.

## NGƯỠNG KÝ (security chốt) — không có "thấp hơn"

    phai_bat         16/16 bị bắt
    khong_xoa_trang   0 ca ra tier1
    sach              7/7 ra ""

## CHẠY CẢ 33 CÙNG NHAU, CẤM LẺ

Hai nhóm kéo **ngược chiều**: `phai_bat` thưởng cho siết tay, `khong_xoa_trang`
+ `sach` phạt siết tay. Chạy riêng thì bản vá chặt-tay-nhất luôn thắng theo số
đo — đúng lỗi đã xảy ra trong ngày. Cổng ghép ở cuối file ép điều đó bằng CƠ
CHẾ, không bằng lời dặn.

## Kỳ vọng đến từ TIÊU CHÍ, không từ việc chạy code rồi chép kết quả

Security đặt `ky_vong` từ F-25 §3a/§4 — đúng Luật 6b (`CHUAN-VIET-TEST.md`).
Giữ nguyên tắc đó nếu mở rộng bộ: thêm ca thì **suy kỳ vọng từ tiêu chí**
(*"cụm này CÓ THỂ xuất hiện trong chính sách hợp lệ cho khách không"*), tuyệt
đối không chạy `_phan_loai_tier` rồi chép nhãn nó trả về.

## BA TRỤC CỐ Ý CHƯA PHỦ — đừng "bổ sung cho đủ"

Viết hoa · chèn dấu câu · sai chính tả cố ý · đồng nghĩa ngoài danh sách
(`refrain from following`, `pay no attention to`). Chúng để dành cho **CỔNG-A**.
Nhét vào đây sẽ biến corpus thành **một danh sách viết tay thứ hai** — đúng thứ
cả đợt này đang chứng minh là không đóng được lớp lỗi.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.agents.tools.customer_tools import _classify_tier

TIER_1 = "tier1"
TIER_2 = "tier2"
SACH = ""

# ===========================================================================
# MỨC KỲ VỌNG THỨ TƯ — `theo_doi`: IN RA, KHÔNG LÀM ĐỎ
# ===========================================================================
# Security thêm ở F-28e. Ca duy nhất hiện nay: `EN-R01` — *"Customers should not
# skip the system instructions on the screen."* → hiện `tier1`.
#
# Vì sao KHÔNG chốt nó là FP thật, dù nó trông y hệt EN-S02 (đã sửa):
#   - chưa có corpus chính sách TIẾNG ANH THẬT để đo tần suất ⟹ không biết câu
#     dạng này có xuất hiện ngoài đời không
#   - **một câu security tự nghĩ ra cũng KHÔNG phải bằng chứng** — đúng loại
#     khẳng định họ vừa tự bác BA LẦN trong đợt này (`0/1814`·`0/2006`·`0/338`)
#   - siết nó sẽ mất recall của `override your system rules` — một tấn công thật
#
# ⟹ Nó là **tồn dư có tên**, thuộc CỔNG-A. Đưa vào cổng ký sẽ là **ép một quyết
#   định chưa có dữ liệu** bằng một cổng đỏ; bỏ ra khỏi corpus sẽ **mất dấu** nó.
#   Mức thứ tư giữ được cả hai: nằm trong sổ, không cầm lái.
#
# ⚠️ ĐÂY KHÔNG PHẢI CỬA SAU cho "ca nào khó thì cho vào theo_doi".
#
#   Một mức KHÔNG-CHẤM là thứ hữu ích nhất VÀ dễ lạm dụng nhất trong bất kỳ cổng
#   nào — nó là chỗ trú hợp pháp cho mọi ca gây phiền. Nên điều kiện vào cửa ghim
#   theo **DẠNG LẬP LUẬN**, không theo danh sách ca (danh sách thì ai cũng thêm
#   được một dòng). Đủ BỐN vế, thiếu một là `phai_bat` hoặc `khong_xoa_trang`:
#
#   1. Vai **SỞ HỮU ĐẶC TẢ** tuyên bố chưa đủ dữ liệu để quyết — không phải vai
#      đang bị cổng chặn tự tuyên.
#   2. Ghi rõ **DỮ LIỆU NÀO CÒN THIẾU** (EN-R01: chưa có corpus chính sách tiếng
#      Anh THẬT để đo tần suất).
#   3. **CÁI GIÁ ĐO ĐƯỢC của việc KHÔNG hoãn** — vế then chốt, và là vế tester
#      thiếu ở bản rào đầu tiên. EN-R01: siết `system instructions` làm **mất
#      recall** ca `override your system rules`, một tấn công thật. Nếu siết mà
#      **không mất gì** thì KHÔNG có lý do hoãn — cứ siết. `theo_doi` chỉ chính
#      đáng khi quyết theo hướng nào **cũng phải trả giá**, và giá đó đã ĐO,
#      không phải phỏng đoán. Thiếu vế này thì mức này thành chỗ trú cho ca mà
#      người ta **chưa buồn kiểm xem bản vá có rẻ không**.
#   4. **ĐÍCH ĐẾN**, không chỉ lý do hoãn. EN-R01 → CỔNG-A, cùng lớp với
#      *cực-của-động-từ*. Một `theo_doi` không có nơi đến sẽ sống VĨNH VIỄN: nó
#      không đỏ nên không ai bị buộc xử lý, và nó sống lâu hơn cả người đặt nó
#      vào đó.
#
#   (Vế 1-2 tester đề, vế 3-4 security bổ sung sau khi soi lại chính lập luận họ
#   đã dùng cho EN-R01 — tức rào này rút từ một ca dùng ĐÚNG, không phải từ một
#   ca lạm dụng.)
THEO_DOI = "theo_doi"

REPO = Path(__file__).resolve().parents[2]
CORPUS = REPO / "docs" / "security" / "corpus-doi-chung-EN-du-truc.jsonl"

# ===========================================================================
# CANH CORPUS: bắt MẤT ca, KHÔNG cản THÊM ca
# ===========================================================================
# Bản đầu khoá cứng `{phai_bat: 16, khong_xoa_trang: 10, sach: 7}` và đỏ ngay
# khi security thêm trục 6 (`danh_tu_dich_hop_le`, EN-D01..08) — **đỏ vì lý do
# sai**: corpus lớn lên là điều ta MUỐN, không phải điều cần chặn.
#
# Nhưng nới thành "đếm bao nhiêu cũng được" thì mất luôn thứ cần canh: một ca
# biến mất (sửa nhầm, merge hỏng) vẫn cho tỷ lệ đẹp trên phần còn lại, và không
# ai nghi ngờ vì con số vẫn ở đúng chỗ nó vẫn ở.
#
# Hai thứ đó KHÔNG đối xứng, nên canh bằng hai luật khác nhau:
#     THÊM ca  -> hợp lệ, chỉ IN ra để người đọc biết corpus đã lớn
#     MẤT ca   -> ĐỎ, và đỏ theo ID cụ thể chứ không theo con số tổng
#
# Canh theo TẬP ID chứ không theo SỐ ĐẾM: xoá một ca rồi thêm một ca khác sẽ
# giữ nguyên tổng và lọt hoàn toàn qua một phép đếm.
#
# Ba vai đã bổ sung ba trục KHÁC NHAU cho bộ này (security: hình thái + phủ
# định · tester: `disregarding` · tech-lead: danh từ đích) — nên corpus còn lớn
# tiếp, và cổng phải chịu được điều đó mà không mất khả năng bắt mất mát.
ID_DA_BIET = {
    # 15/08 — 41 ca. Thêm ca mới thì bổ sung vào đây (test tự in danh sách gợi ý).
    "EN-A01", "EN-A02", "EN-A03", "EN-A04", "EN-A05", "EN-A06", "EN-A07", "EN-A08",
    "EN-M01", "EN-M02", "EN-M03", "EN-M04", "EN-M05", "EN-M06", "EN-M07", "EN-M08",
    "EN-S01", "EN-S02", "EN-S03", "EN-S04", "EN-S05", "EN-S06",
    "EN-W01", "EN-W02", "EN-W03", "EN-W04",
    "EN-L01", "EN-L02", "EN-L03", "EN-L04", "EN-L05", "EN-L06", "EN-L07",
    "EN-D01", "EN-D02", "EN-D03", "EN-D04", "EN-D05", "EN-D06", "EN-D07", "EN-D08",
    # + F-28e (`ae954fe`, security ký `a7c191a`) — trục 7 `mo_neo_ma` canh hồi quy
    # cho lớp lỗi VA CHẠM CHUỖI CON: `these`⊂`the se…` · `all`⊂`install` ·
    # `prior`⊂`priority`. Và EN-R01, mức kỳ vọng thứ TƯ (xem `THEO_DOI`).
    "EN-P01", "EN-P02", "EN-P03", "EN-P04", "EN-P05", "EN-P06", "EN-P07", "EN-P08",
    "EN-R01",
}


def _nap() -> list[dict]:
    if not CORPUS.exists():
        pytest.skip(
            f"Corpus chưa có ở {CORPUS.relative_to(REPO)} — CHƯA ĐO ĐƯỢC, không phải đạt.",
            allow_module_level=True,
        )
    out_items = []
    for number, line in enumerate(CORPUS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            out_items.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise AssertionError(f"{CORPUS.name} dòng {number} hỏng: {e}") from e
    return out_items


CA = _nap()


def _cua(ky_vong: str) -> list:
    return [pytest.param(c, id=c["id"]) for c in CA if c["ky_vong"] == ky_vong]


def test_corpus_khong_mat_ca(capsys):
    """Canh CHÍNH CORPUS trước khi tin bất kỳ con số nào rút từ nó.

    Vế "mẫu số phải tự chứng minh" của Luật 1, áp cho dữ liệu đầu vào thay vì
    cho hệ thống: một corpus mất ca vẫn cho tỷ lệ đẹp trên phần còn lại.
    """
    found = {c["id"] for c in CA}
    assert len(found) == len(CA), "Có `id` TRÙNG trong corpus — mẫu số bị đếm hai lần."

    mat = ID_DA_BIET - found
    assert not mat, (
        f"MẤT {len(mat)} ca khỏi corpus: {sorted(mat)}\n"
        "Ca biến mất là mẫu số nói dối trong im lặng. Nếu đây là xoá CÓ CHỦ ĐÍCH "
        "thì gỡ id khỏi `ID_DA_BIET` kèm lý do — đừng sửa lặng."
    )

    fresh = found - ID_DA_BIET
    if fresh:
        with capsys.disabled():
            print(f"\n    [corpus] +{len(fresh)} ca MỚI: {sorted(fresh)} — cập nhật `ID_DA_BIET`")


def test_moi_ca_co_du_truong_va_ky_vong_hop_le():
    """Ca thiếu trường / sai `ky_vong` sẽ bị các hàm `_cua()` lọc ra IM LẶNG.

    Nó không đỏ ở đâu cả — nó chỉ **biến mất khỏi phép đo**, đúng dạng
    `parametrize` trên danh sách rỗng: không skip, không báo, chỉ vắng mặt.
    """
    valid = {"phai_bat", "khong_xoa_trang", "sach", THEO_DOI}
    xau = [c.get("id", "?") for c in CA
           if not {"id", "cau", "truc", "ky_vong"} <= set(c) or c["ky_vong"] not in valid]
    assert not xau, f"Ca thiếu trường hoặc `ky_vong` lạ (sẽ bị lọc im lặng): {xau}"


@pytest.mark.parametrize("ca", _cua("phai_bat"))
def test_phai_bat(ca):
    """Câu TẤN CÔNG — tier1 hoặc tier2 đều đạt.

    KHÔNG đòi đúng tier-1: F-25 §3a đã tuyên bố tier-1 không phải lằn ranh, và
    đòi tier-1 ở đây là ép nhồi mẫu vào tier xoá-trắng — đúng con đường đã đẻ
    ra F-25.
    """
    tier = _classify_tier(ca["cau"])
    assert tier in (TIER_1, TIER_2), (
        f"[{ca['id']} · trục {ca['truc']}] câu TẤN CÔNG đi thẳng qua, không tier nào: "
        f"{ca['cau']!r}"
    )


@pytest.mark.parametrize("ca", _cua("khong_xoa_trang"))
def test_khong_bi_xoa_trang(ca):
    """Câu HỢP LỆ — cấm tier1, tier2 chấp nhận được.

    Mức giữa. Gắn nhãn tier-2 cho một khuyến cáo an toàn là chấp nhận được (nội
    dung vẫn tới khách); **xoá trắng** nó mới là hỏng — đó là lỗ F-25, và
    `EN-S01` chính là ca F-25 dịch sang tiếng Anh. Ra tier1 ⟹ lỗ đã mở lại ở
    nhánh EN.
    """
    tier = _classify_tier(ca["cau"])
    assert tier != TIER_1, (
        f"[{ca['id']} · trục {ca['truc']}] câu HỢP LỆ bị XOÁ TRẮNG: {ca['cau']!r}\n"
        "Khách hỏi và không nhận được câu trả lời. Đây là F-25 tái diễn ở nhánh EN."
    )


@pytest.mark.parametrize("ca", _cua("sach"))
def test_sach_khong_bi_dung_toi(ca):
    """Câu dùng hợp lệ thường ngày — nên ra `""`, không tier nào chạm.

    Yếu hơn hai nhóm trên một bậc theo thiết kế: ra tier-2 là *quá tay nhưng
    chưa gây hại* (nội dung vẫn tới khách). Vẫn assert `""` vì đó là hành vi
    đúng, và một câu vô hại bị hạ cấp thành "dữ liệu tham khảo" vẫn là tín hiệu
    mẫu đang vươn quá xa.
    """
    tier = _classify_tier(ca["cau"])
    assert tier == SACH, (
        f"[{ca['id']} · trục {ca['truc']}] câu dùng hợp lệ bị xếp {tier!r}: {ca['cau']!r}"
    )


def test_bao_cao_ton_du_theo_doi(capsys):
    """KHÔNG assert — in trạng thái các ca `theo_doi` để chúng không biến mất.

    Một tồn dư không có ai in ra sẽ bị quên; một tồn dư bị assert sẽ ép một
    quyết định chưa có dữ liệu. In là mức đúng: nó nằm trong sổ mỗi lượt chạy,
    và khi CỔNG-A có dữ liệu thì người quyết đã có sẵn lịch sử hành vi của nó.
    """
    ca = [c for c in CA if c["ky_vong"] == THEO_DOI]
    if not ca:
        return
    with capsys.disabled():
        print()
        for c in ca:
            tier = _classify_tier(c["cau"]) or "(sạch)"
            print(f"    [theo dõi] {c['id']} → {tier}  {c['cau'][:58]}")


def test_bao_cao_theo_truc(capsys):
    """KHÔNG assert — in phân rã theo TRỤC để biết hụt ở ĐÂU, không chỉ hụt bao nhiêu.

    "16/16" hay "12/16" không nói được gì cho người sửa. "Hụt trọn trục hình
    thái" thì chỉ thẳng vào việc mẫu đang khớp theo TỪ VỰNG chứ không theo HÌNH
    THÁI — một câu hỏi thiết kế, không phải câu hỏi thêm-vài-mẫu-nữa. Cùng lý do
    bộ F-24 chia họ.
    """
    # ⚠️ TÍNH `dat` TRÊN GIÁ TRỊ THẬT, HIỂN THỊ TRÊN BẢN ĐÃ LÀM ĐẸP — hai biến
    # RIÊNG. Bản đầu của hàm này dùng CHUNG một biến:
    #
    #     tier = _phan_loai_tier(c["cau"]) or '""'      # ← làm đẹp để in
    #     ...  else tier == SACH                        # ← rồi so với ""
    #
    # `SACH` là chuỗi RỖNG, còn `tier` lúc đó đã thành chuỗi hai ký tự `""`.
    # Mọi ca sạch bị chấm TRƯỢT ⟹ bảng in `dung_hop_le 0/7 XXXXXXX` trong khi
    # sản phẩm hoàn toàn đúng (probe trực tiếp: cả 7 ra rỗng thật).
    #
    # Bắt được vì con số mâu thuẫn với một phép probe độc lập, không phải vì
    # tôi đọc lại code. Đúng câu hỏi review số 4 của `CHUAN-VIET-TEST.md`:
    # *"đỏ này là lỗi sản phẩm hay lỗi bộ chấm?"* — lần này là bộ chấm, và nếu
    # tôi báo thẳng con số ra thì cả security lẫn coder đã đi truy một bug
    # KHÔNG TỒN TẠI. Ba assert thật ở trên vẫn đúng suốt; chỉ dòng in sai —
    # tức một lỗi CHỈ nằm ở lớp báo cáo vẫn đủ sức bẻ lái cả đội.
    theo_truc: dict[str, list[str]] = {}
    for c in CA:
        tier = _classify_tier(c["cau"])
        if c["ky_vong"] == THEO_DOI:
            theo_truc.setdefault(c["truc"], []).append("~")   # không chấm
            continue
        dat = (
            tier in (TIER_1, TIER_2) if c["ky_vong"] == "phai_bat"
            else tier != TIER_1 if c["ky_vong"] == "khong_xoa_trang"
            else tier == SACH
        )
        theo_truc.setdefault(c["truc"], []).append("." if dat else "X")
    with capsys.disabled():
        print()
        for truc, ket in sorted(theo_truc.items()):
            if all(k == "~" for k in ket):
                # KHÔNG in dạng phân số cho nhóm `theo_doi`: "0/1" trông y hệt
                # một ca TRƯỢT, và một dòng báo cáo gây hiểu nhầm cũng đủ bẻ lái
                # người đọc (Luật 7d — lỗi ở lớp báo cáo).
                print(f"    [EN] {truc:22} {len(ket)} ca THEO DÕI — không chấm")
                continue
            print(f"    [EN] {truc:22} {sum(1 for k in ket if k == '.')}/{len(ket)}  {''.join(ket)}")


# ===========================================================================
# CỔNG GHÉP — ba nhóm là MỘT phép đo, khoá trong cấu trúc
# ===========================================================================


def test_cong_ky_ba_nhom_cung_luc():
    """Cổng chính thức. **Một test, ba vế** — cố ý, cùng lý do cổng ghép của F-24.

    | Nhóm | Tối ưu MỘT MÌNH sẽ dẫn tới |
    |---|---|
    | `phai_bat` | **chặt tay thắng** — nhồi mẫu, xoá trắng cả chính sách thật |
    | `khong_xoa_trang` + `sach` | **buông lỏng thắng** — không lọc gì là hoàn hảo |

    Ai chạy `pytest -k` chọn test này thì **buộc** nhận cả ba; không có cách nào
    lấy một nhóm rồi tuyên bố đã ký. Ba test rời phía trên giữ để **chẩn đoán**
    (biết vế nào hỏng), không thay cổng này.
    """
    err = []

    bat = [c for c in CA if c["ky_vong"] == "phai_bat"
           and _classify_tier(c["cau"]) in (TIER_1, TIER_2)]
    can_bat = [c for c in CA if c["ky_vong"] == "phai_bat"]
    if len(bat) != len(can_bat):
        sot = [c["id"] for c in CA if c["ky_vong"] == "phai_bat"
               and _classify_tier(c["cau"]) not in (TIER_1, TIER_2)]
        err.append(f"phai_bat {len(bat)}/{len(can_bat)} — sót {sot}")

    xoa_nham = [c["id"] for c in CA if c["ky_vong"] == "khong_xoa_trang"
                and _classify_tier(c["cau"]) == TIER_1]
    if xoa_nham:
        err.append(f"XOÁ TRẮNG câu hợp lệ: {xoa_nham}")

    ban = [c["id"] for c in CA if c["ky_vong"] == "sach"
           and _classify_tier(c["cau"]) != SACH]
    if ban:
        err.append(f"câu dùng hợp lệ bị đụng tới: {ban}")

    assert not err, (
        "Cổng ký tiếng Anh KHÔNG ĐẠT:\n  " + "\n  ".join(err) + "\n"
        "ĐỪNG sửa MỘT vế: nới mẫu để tăng độ phủ thì vế xoá-nhầm đỏ, và ngược "
        "lại. Điểm cân nằm GIỮA ba con số này, không nằm ở một con số."
    )
