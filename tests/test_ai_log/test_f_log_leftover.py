"""F-LOG / F-LOG-2 — nhánh `leftover` của `scripts/submit_log.py`, đo HỘP ĐEN.

Nguồn đặc tả: `docs/giao-viec/2026-08-15-do-luong-F-LOG.md` (tech-lead đo, PO-agent
chạy lại độc lập, khớp từng số). Hai script gốc sống ở scratchpad `/private/tmp`
gắn phiên tech-lead — **phiên đóng là bằng chứng bốc hơi**, nên chúng được port
vào đây để tồn tại cùng repo. Đây là việc PO-agent giao chính thức 15/08.

## VÌ SAO NHÁNH NÀY ĐÁNG MỘT FILE TEST RIÊNG

`submit_log.py` gửi tối đa `BATCH_LIMIT` (500) bản ghi mỗi lượt; phần dư
("leftover") được ghi NGƯỢC lại `session.jsonl` để lượt sau gửi tiếp. Nhánh đó
**CHƯA TỪNG CHẠY THẬT**: lượt 15/08 chỉ có 73 bản ghi, dưới ngưỡng 500.

Nó sắp chạy **19 lượt liên tiếp trên 9.133 dòng backlog P-121** — deliverable #4.
Tức lần đầu tiên nhánh này chạy thật sẽ là lúc nó xử lý toàn bộ bằng chứng học
tập của một dự án. Một nhánh **không ai canh** (Luật 14) đứng ngay trước một
việc không làm lại được.

## HỘP ĐEN — VÌ SAO CÁCH ĐO NÀY KHÔNG VI PHẠM §4

Không import, không đọc logic của `submit_log.py`. Test chạy nó **qua
subprocess** đối với một **server HTTP giả** trên cổng ngẫu nhiên, với
`AI_LOG_DIR` trỏ vào `tmp_path` của pytest. Ba biến môi trường
(`AI_LOG_SERVER`/`AI_LOG_API_KEY`/`AI_LOG_DIR`) là **giao diện**, không phải nội
dung — cùng hạng với "bảng mã" ở `tests/CHUAN-VIET-TEST.md` Luật 6b.

Kỳ vọng dẫn từ ĐẶC TẢ (hồ sơ F-LOG), không từ hành vi quan sát được.

## AN TOÀN — KHÔNG ĐỤNG GÌ THẬT

`.ai-log` thật: không đụng · cây làm việc: không đụng · mạng: không cần
(`127.0.0.1`, cổng 0 = hệ điều hành tự cấp).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "submit_log.py"

# Từ đặc tả (`docs/STATE.md`: "BATCH_LIMIT=500 mỗi lần push ⟹ cần ~19 lượt"),
# KHÔNG đọc ra từ script — nếu script đổi hằng số này mà đặc tả không đổi thì
# test phải ĐỎ, đó là điểm của việc lấy số từ đặc tả.
BATCH_LIMIT = 500


class _ServerGia(BaseHTTPRequestHandler):
    """Nhận POST, trả 202. `ngu_giay` (biến lớp) để dựng cửa sổ đua."""

    ngu_giay = 0.0
    da_nhan: list = []

    def do_POST(self):  # noqa: N802 — tên do BaseHTTPRequestHandler quy định
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        try:
            type(self).da_nhan.append(json.loads(body.decode()))
        except Exception:  # noqa: BLE001 — thân không phải JSON cũng là dữ liệu
            type(self).da_nhan.append({"entries": []})
        time.sleep(type(self).ngu_giay)
        self.send_response(202)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


@pytest.fixture
def server():
    """Server giả trên cổng ngẫu nhiên; tự dọn sau mỗi test."""
    _ServerGia.da_nhan = []
    _ServerGia.ngu_giay = 0.0
    srv = HTTPServer(("127.0.0.1", 0), _ServerGia)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


def _dung_san(thu_muc: Path, so_dong: int, hong_tai: int | None = None) -> Path:
    """Dựng `session.jsonl` với `so_dong` bản ghi, tuỳ chọn chèn 1 dòng JSON HỎNG."""
    thu_muc.mkdir(parents=True, exist_ok=True)
    f = thu_muc / "session.jsonl"
    with open(f, "w", encoding="utf-8") as out:
        for i in range(so_dong):
            if hong_tai is not None and i == hong_tai:
                # Dòng bị cắt giữa chừng — đúng thứ xảy ra khi tiến trình chết
                # lúc đang ghi. Dấu "HỎNG" để truy được nó ở mọi nơi.
                out.write(
                    f'{{"id": {i}, "noi_dung": "dòng HỎNG bị cắt giữa chừn\n'
                )
                continue
            out.write(
                json.dumps({"id": i, "noi_dung": f"bản ghi tiếng Việt {i}"},
                           ensure_ascii=False) + "\n"
            )
    return f


def _chay(san: Path, srv: HTTPServer) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AI_LOG_SERVER"] = f"http://127.0.0.1:{srv.server_address[1]}/submit"
    env["AI_LOG_API_KEY"] = "khoa-gia-cho-test"
    env["AI_LOG_DIR"] = str(san)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env, capture_output=True, text=True, cwd=str(REPO), timeout=60,
    )


def _doc(p: Path) -> list[str]:
    return [d for d in p.read_text(encoding="utf-8").splitlines() if d.strip()]


def _dong_archive(san: Path) -> list[str]:
    """Archive CHÍNH — bằng chứng "đã nộp thành công". LOẠI `*.hong.jsonl`.

    ⚠️ TÁCH HAI LOẠI FILE LÀ CÓ CHỦ ĐÍCH, đừng "dọn" bằng cách glob hết:
    bản vá F-LOG (`cc07dd3`) giữ dòng không parse được ở `archive/*.hong.jsonl`
    RIÊNG, không trộn vào archive chính — để archive chính giữ được tính chất
    "mỗi dòng một JSON hợp lệ".

    Nếu phép đếm ở đây gộp cả hai thì một dòng **KHÔNG hề được gửi** sẽ bị tính
    là "đã nộp". Đó là mẫu số nói dối theo hướng ĐẸP HƠN sự thật — nguy hơn
    hướng ngược lại, vì hướng xấu thì tự lộ còn hướng đẹp thì im lặng che.
    Bản đầu của hàm này glob `*.jsonl` và mắc đúng lỗi đó.
    """
    d = san / "archive"
    if not d.exists():
        return []
    ra: list[str] = []
    for f in sorted(d.glob("*.jsonl")):
        if f.name.endswith(".hong.jsonl"):
            continue
        ra += _doc(f)
    return ra


def _dong_hong(san: Path) -> list[str]:
    """Dòng KHÔNG parse được, giữ nguyên văn — không phải bằng chứng đã nộp."""
    d = san / "archive"
    if not d.exists():
        return []
    ra: list[str] = []
    for f in sorted(d.glob("*.hong.jsonl")):
        ra += _doc(f)
    return ra


def _thu_tu_id(f: Path) -> list[int]:
    return [
        json.loads(dong)["id"]
        for dong in f.read_text(encoding="utf-8").splitlines() if dong.strip()
    ]


# ===========================================================================
# ĐÓNG DẤU VẬT — lỗ của chính bộ đo này, phát hiện 15/08 sau khi nó tự bắn
# ===========================================================================
# Hai script gốc IN băm `submit_log.py` ở dòng đầu ("VẬT ĐANG THỬ"). Khi port
# sang pytest tôi **làm rơi mất bước đó** — và nó không vô hại:
#
# Dấu `he_thong` của dự án băm `src/**/*.py`. Nhưng VẬT của file test này là
# `scripts/submit_log.py`, **không nằm trong `src/`**. Nên mọi con số ở đây
# nằm ngoài tầm phủ của dấu chuẩn: `he_thong` có thể đứng yên tuyệt đối trong
# khi vật đang bị sửa ngay dưới chân phép đo.
#
# Đúng bài học Luật 4 ("ghim một nửa thì nửa kia trôi trong im lặng"), lần này
# nửa bị trôi là nửa mà cái ghim chuẩn của dự án KHÔNG với tới. Ca thật: F-LOG
# được vá giữa phiên, `git status scripts/` bẩn, mà `he_thong` không phản ánh
# một chữ nào.


def bam_vat() -> str:
    """Băm VẬT ĐANG THỬ. Dùng để dán nhãn mọi con số của file này."""
    import hashlib

    return hashlib.sha256(SCRIPT.read_bytes()).hexdigest()[:12]


def test_in_dau_vat(capsys):
    """KHÔNG assert — in băm để mọi kết quả của file này dán được nhãn.

    Không assert vào một giá trị băm cụ thể: làm thế thì mỗi lần vá hợp lệ đều
    đỏ, và người ta sẽ học cách sửa hằng số cho xong — đúng thứ "chép số từ
    suite ra" mà `test_f24_recall_tier1.py` cấm. Vai trò của nó là **dán nhãn**,
    không phải canh cổng.
    """
    with capsys.disabled():
        print(f"\n    [VẬT] scripts/submit_log.py băm={bam_vat()}")


# ===========================================================================
# CA 1 — nhánh leftover chạy đúng: không mất, không TRÙNG LẶP
# ===========================================================================


def test_leftover_gui_du_khong_trung_lap(tmp_path, server):
    """502 dòng · 2 lượt · archive phải có ĐÚNG 502 dòng, 0 trùng.

    Đây là ca canh chính cho 19 lượt sắp chạy trên backlog P-121. Hai chiều hỏng
    đều có giá thật và **ngược nhau**, nên phải đo cả hai bằng cùng một phép:
      - archive < 502  ⟹ MẤT bằng chứng học tập, không lấy lại được
      - archive > 502  ⟹ archive PHÌNH do gửi/lưu trùng, và mọi phép đếm sau này
        dựa trên archive đều sai theo hướng đẹp hơn sự thật

    Đếm `id` DUY NHẤT chứ không chỉ đếm dòng: 502 dòng gồm 2 bản sao của cùng
    một bản ghi vẫn ra "502" nếu chỉ đếm dòng — đúng dạng xanh giả mà Luật 1
    cảnh báo.
    """
    san = tmp_path / "san"
    _dung_san(san, BATCH_LIMIT + 2)

    for _ in range(2):
        r = _chay(san, server)
        assert r.returncode == 0, f"submit_log.py thoát {r.returncode}: {r.stderr}"

    arc = _dong_archive(san)
    ids = [json.loads(dong)["id"] for dong in arc]

    assert len(arc) == BATCH_LIMIT + 2, (
        f"archive có {len(arc)} dòng, phải có {BATCH_LIMIT + 2}. "
        "Thiếu = mất bằng chứng; thừa = archive phình do trùng lặp."
    )
    assert len(set(ids)) == len(ids), (
        f"archive có {len(ids) - len(set(ids))} dòng TRÙNG LẶP — nhánh leftover "
        "đang archive lại thứ đã archive."
    )
    assert set(ids) == set(range(BATCH_LIMIT + 2)), "Tập id không khớp tập đã ghi vào."


def test_server_nhan_dung_tong_so_ban_ghi(tmp_path, server):
    """Vế thứ hai của CA 1, tách riêng: archive đúng KHÔNG chứng minh đã GỬI đúng.

    Một bản cài đặt archive đủ 502 dòng mà chỉ POST 500 lên server sẽ qua được
    test trên nhưng **mất 2 bản ghi ở phía nhận** — tức grading server thiếu dữ
    liệu trong khi mọi dấu vết cục bộ nói là xong. Hai câu hỏi khác nhau, hai
    assert khác nhau. (Cùng lý do bộ đo O1-O4 phải đọc cặp số "ĐẠT" và "🔇"
    cùng nhau thay vì đọc riêng.)
    """
    san = tmp_path / "san"
    _dung_san(san, BATCH_LIMIT + 2)
    for _ in range(2):
        _chay(san, server)

    tong = sum(len(b.get("entries", [])) for b in _ServerGia.da_nhan)
    assert tong == BATCH_LIMIT + 2, (
        f"Server nhận {tong} bản ghi, phải nhận {BATCH_LIMIT + 2}. "
        "archive cục bộ có thể vẫn đủ — đó là lý do assert này tách riêng."
    )


# ===========================================================================
# CA 2 — F-LOG: dòng JSON hỏng MẤT HẲN.  ĐỎ CÓ CHỦ ĐÍCH.
# ===========================================================================


def test_dong_json_hong_phai_con_truy_duoc(tmp_path, server):
    """F-LOG — REGRESSION GATE (trước 15/08 là ca tái lập finding, nay đã vá).

    ## Lịch sử, giữ lại vì cách nó được phát hiện mới là phần đáng giá

    Ca này viết ra để **tái lập** F-LOG: một dòng JSON hỏng biến mất khỏi MỌI
    dấu vết — không lên server, không vào archive, không còn ở `session.jsonl`.
    Đo A/B hai revision: `eadcca7^` archive 10 dòng CÒN dòng hỏng · `eadcca7`
    archive 9 dòng MẤT HẲN ⟹ hồi quy, không phải vốn đã thế.

    Nó mang `xfail(strict=True)`. Coder vá ở `cc07dd3` **mà không nhắn ai**, và
    `strict=True` tự biến "qua được" thành ĐỎ (`XPASS`) — bộ test tự phát hiện
    bản vá và tự đòi được gỡ marker. Yêu cầu *"chỉ chuyển xanh SAU khi vá"* là
    một CƠ CHẾ chứ không phải lời nhắc trong tin nhắn, nên nó không phụ thuộc
    vào việc ai có nhớ hay không.

    ## Vì sao assert ba vế chứ không chỉ "còn truy được"

    Vế "còn truy được" một mình sẽ XANH cho một bản vá **trộn dòng hỏng vào
    archive chính** — thứ đổi lỗ mất-dữ-liệu lấy lỗ hỏng-định-dạng (archive
    chính mất tính chất "mỗi dòng một JSON hợp lệ") **và** thổi phồng số "đã
    nộp" bằng một dòng chưa từng được gửi.
    """
    san = tmp_path / "san"
    _dung_san(san, 10, hong_tai=3)
    r = _chay(san, server)

    hong = _dong_hong(san)
    chinh = _dong_archive(san)

    # (1) GIỮ NGUYÊN VĂN — vế gốc của F-LOG.
    assert any("HỎNG" in d for d in hong), (
        f"Dòng JSON hỏng không còn truy được. archive hỏng={hong!r}. "
        "Đây là F-LOG tái diễn: mất dữ liệu IM LẶNG."
    )

    # (2) KHÔNG bị tính là đã nộp — archive chính là bằng chứng "đã gửi thành
    #     công", một dòng chưa từng gửi mà nằm trong đó là mẫu số nói dối.
    assert not any("HỎNG" in d for d in chinh), (
        "Dòng hỏng lọt vào archive CHÍNH — nó chưa từng được gửi, nên có mặt ở "
        "đó là thổi phồng số 'đã nộp'."
    )
    assert len(chinh) == 9, f"archive chính phải có đúng 9 dòng hợp lệ, có {len(chinh)}."

    # (3) HỎNG KHÔNG ĐƯỢC IM LẶNG — người vận hành phải biết có dòng bị bỏ lại.
    #     Thiếu vế này thì một bản vá "giữ file nhưng không báo" vẫn xanh, và ta
    #     quay lại đúng vấn đề gốc ở dạng nhẹ hơn: dữ liệu còn đó nhưng không ai
    #     biết để đi tìm.
    assert "hong" in r.stderr.lower() or "hỏng" in r.stderr.lower(), (
        f"Không có cảnh báo nào trên stderr về dòng bị bỏ lại. stderr={r.stderr!r}"
    )


# ===========================================================================
# CA 3 + PHẦN B — CÙNG MỘT CÂU HỎI, HAI KỊCH BẢN, HAI KẾT QUẢ NGƯỢC NHAU
# ===========================================================================
# ⚠️ ĐỌC TRƯỚC KHI "DỌN CHO GỌN": hai test dưới đây trông TRÙNG NHAU. Chúng
# không trùng, và bỏ cái thứ hai là tự tạo một xanh giả.
#
#   test_thu_tu_..._tuan_tu     -> ĐẠT   [500, 501, 900, 901]
#   test_thu_tu_..._dong_thoi   -> TRƯỢT [900, 901, 500, 501]
#
# Khác biệt DUY NHẤT: ca tuần tự ghi 2 dòng mới SAU KHI lượt chạy kết thúc; ca
# đồng thời ghi chúng GIỮA LÚC POST đang treo (server ngủ 1.5s, luồng phụ ghi ở
# giây 0.6).
#
# ⟹ **F-LOG-2 CHỈ HIỆN RA DƯỚI ĐỒNG THỜI THẬT.** Giữ một mình ca tuần tự thì nó
# sẽ "chứng minh" thứ tự đúng và bỏ sót hoàn toàn lỗi. Đây là luật "ca đối chứng
# bắt buộc" ở chiều KỊCH BẢN thay vì chiều dữ liệu — và là lý do tech-lead +
# PO-agent yêu cầu port CẢ HAI script chứ không gộp làm một.
#
# Nó cũng có thật ngoài đời: hook `pre-push` chạy `submit_log.py` trong khi
# phiên Claude vẫn đang ghi bản ghi mới vào `session.jsonl`. Cửa sổ đua không
# phải giả định.


def test_thu_tu_van_dung_khi_ghi_tuan_tu(tmp_path, server):
    """Ghi thêm SAU khi lượt chạy xong — thứ tự cũ-trước-mới phải giữ.

    ĐẠT. Test này tồn tại để làm ĐỐI CHỨNG cho ca đồng thời bên dưới: nó chứng
    minh rằng khi KHÔNG có đua, cơ chế leftover xếp thứ tự đúng ⟹ cái sai ở ca
    kia đến từ ĐỒNG THỜI, không phải từ logic xếp thứ tự nói chung.
    """
    san = tmp_path / "san"
    f = _dung_san(san, BATCH_LIMIT + 2)
    _chay(san, server)

    with open(f, "a", encoding="utf-8") as out:
        for i in (900, 901):
            out.write(json.dumps({"id": i, "noi_dung": "MỚI"}, ensure_ascii=False) + "\n")

    assert _thu_tu_id(f) == [500, 501, 900, 901], (
        "Ngay cả khi KHÔNG có đua, thứ tự đã sai — hỏng nặng hơn F-LOG-2."
    )


@pytest.mark.slow
def test_thu_tu_phai_dung_ca_khi_ghi_dong_thoi(tmp_path, server):
    """Hook ghi bản ghi MỚI trong lúc `submit_log.py` đang treo ở POST.

    REGRESSION GATE (trước `e321780` là ca tái lập finding F-LOG-2).

    Đây là ca duy nhất trong file bắt được F-LOG-2, và nó chỉ bắt được vì có
    ĐỒNG THỜI THẬT — không mock, không monkeypatch: server giả ngủ 1.5 giây,
    một luồng phụ ghi vào `session.jsonl` ở giây 0.6. Ca tuần tự ngay bên trên
    báo ĐẠT cho cùng câu hỏi — giữ cả hai chính vì thế.

    Lịch sử: `[900, 901, 500, 501]` trước vá -> `[500, 501, 900, 901]` sau
    `e321780` (ghép cũ+mới rồi `os.replace` nguyên tử, thay `open(..., "a")`).
    Ca này mang `xfail(strict=True)`; coder vá mà không nhắn ai, `XPASS` tự báo
    lỗi và đòi gỡ marker — lần THỨ HAI trong cùng một phiên cơ chế đó tự bắn.

    Kỳ vọng: bản ghi cũ (500, 501 — leftover) phải đứng TRƯỚC bản ghi mới
    (900, 901). `session.jsonl` là hàng đợi theo thời gian; đảo thứ tự nghĩa là
    lượt push sau gửi log lộn xộn, và với 19 lượt trên 9.133 dòng thì sai lệch
    tích luỹ qua từng lượt.
    """
    san = tmp_path / "san"
    f = _dung_san(san, BATCH_LIMIT + 2)
    _ServerGia.ngu_giay = 1.5

    def hook_ghi():
        time.sleep(0.6)  # rơi vào GIỮA lúc POST đang treo
        with open(f, "a", encoding="utf-8") as out:
            for i in (900, 901):
                out.write(json.dumps({"id": i, "noi_dung": "MOI"}, ensure_ascii=False) + "\n")

    t = threading.Thread(target=hook_ghi)
    t.start()
    _chay(san, server)
    t.join()

    ids = _thu_tu_id(f)

    # (1) KHÔNG MẤT — vế phải kiểm TRƯỚC thứ tự. Một bản "vá" ghi đè thẳng
    #     leftover lên file sẽ cho thứ tự [500, 501] rất đúng đắn, vì hai bản
    #     ghi mới đã bị nuốt mất. Đo thứ tự trước khi đo toàn vẹn là tự mở
    #     đường cho một bản vá đổi lỗi-thứ-tự lấy lỗi-mất-dữ-liệu.
    assert sorted(ids) == [500, 501, 900, 901], (
        f"Mất hoặc trùng bản ghi dưới đồng thời: {ids}. Cửa sổ đua không được "
        "phép nuốt bản ghi nào — thứ tự đúng mà thiếu dòng thì tệ hơn."
    )

    # (2) ĐÚNG THỨ TỰ — vế gốc của F-LOG-2.
    assert ids == [500, 501, 900, 901], (
        f"Thứ tự sau đua: {ids}. Bản ghi CŨ (leftover) phải đứng TRƯỚC bản ghi "
        "MỚI — session.jsonl là hàng đợi theo thời gian, lượt push sau đọc theo "
        "thứ tự này."
    )
