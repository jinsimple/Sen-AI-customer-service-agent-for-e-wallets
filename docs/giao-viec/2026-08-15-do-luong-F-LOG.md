# Hồ sơ phép đo F-LOG / F-LOG-2 — bảo tồn để NGƯỜI KHÁC bác được (Luật 10)

> **Vì sao file này tồn tại.** Hai script đo dưới đây do **tech-lead** (`p-226-8f`) viết, ban đầu
> chỉ nằm ở scratchpad `/private/tmp/...` gắn với phiên của họ. Phiên đóng hoặc máy khởi động lại
> là bằng chứng **bốc hơi**, và một đường dẫn chết trong hồ sơ còn tệ hơn không có — nó trông như
> bằng chứng còn sống. Tech-lead chủ động nêu đúng vấn đề này và **từ chối tự chọn chỗ đặt**, vì
> `tests/` là vùng tester còn `scripts/` là **vùng vô chủ** (xem F-ZONE trong `docs/STATE.md`).
>
> **Đây là chỗ đặt TẠM, không phải chỗ đúng cuối cùng.** `docs/` là vùng ghi của PO-agent nên bảo
> tồn được ngay mà không giẫm vùng ai. Khi PO thật chốt F-ZONE, người có thẩm quyền chép nội dung
> dưới đây thành file chạy được ở `scripts/` hoặc `tests/` rồi xoá mục "chỗ đặt tạm" này.
>
> **CA2 và phần B CỐ Ý ĐỎ** — chúng là ca TÁI LẬP FINDING, không phải test hồi quy.
> Đừng ai "sửa cho xanh". Khi F-LOG được vá, CA2 mới được phép chuyển xanh.

## Kết quả — hai lần chạy độc lập, khớp từng số

| Ca | Kỳ vọng | tech-lead | PO-agent chạy lại |
|---|---|---|---|
| CA1 leftover 502 dòng | `502/502/0` ĐẠT | ĐẠT | **ĐẠT** |
| CA2 dòng JSON hỏng | MẤT HẲN (đỏ có chủ đích) | MẤT HẲN | **MẤT HẲN** |
| A/B trước-sau vá | TRƯỚC CÒN · SAU MẤT | đúng vậy | **đúng vậy** |
| B đua thứ tự | `[900,901,500,501]` TRƯỢT | TRƯỢT | **TRƯỢT** |

Băm VẬT lúc PO-agent chạy lại: `submit_log.py` = `ab75391a3e09` (bản SAU vá, `eadcca7`) ·
bản TRƯỚC vá `eadcca7^` = `f1e4950e1df6` · HEAD repo `d8951e3`.
Băm hai script: `thu_nhanh_leftover.py` = `b2e79bf7bc26` · `thu_hoi_quy.py` = `301a1d797e55`
(PO-agent tính lại bằng `shasum -a 256`, khớp con số tech-lead báo — xác minh độc lập).

## ⚠️ Bẫy quan trọng: CA3 và phần B hỏi CÙNG một câu, trả lời NGƯỢC nhau

- `thu_nhanh_leftover.py` **CA3** → `[500, 501, 900, 901]` **ĐẠT**
- `thu_hoi_quy.py` **phần B** → `[900, 901, 500, 501]` **TRƯỢT**

Không phải mâu thuẫn. CA3 ghi hai dòng mới **SAU KHI** lượt chạy kết thúc (tuần tự); phần B ghi
**GIỮA LÚC POST đang treo** (server giả ngủ 1.5s, luồng phụ ghi vào giây 0.6) — đua thật.
⟹ **Lỗi thứ tự F-LOG-2 chỉ hiện ra dưới ĐỒNG THỜI THẬT.** Một test tuần tự sẽ báo xanh và bỏ sót
hoàn toàn. Đây là lý do phải giữ CẢ HAI script: bỏ `thu_hoi_quy.py` đi thì `thu_nhanh_leftover.py`
một mình sẽ "chứng minh" thứ tự đúng — một xanh giả. Cùng họ với luật "ca đối chứng bắt buộc",
nhưng ở chiều KỊCH BẢN chứ không phải chiều dữ liệu.

## Cách chạy lại

```bash
# Cần một python bất kỳ — hai script chỉ dùng THƯ VIỆN CHUẨN.
# Tự dựng sân riêng (san_thu/, san_hq/) cạnh chính nó, tự chạy server giả trên cổng ngẫu nhiên.
# KHÔNG đụng .ai-log thật · KHÔNG đụng cây làm việc · KHÔNG cần mạng.
# thu_hoi_quy.py dùng `git show eadcca7^:scripts/submit_log.py` — read-only, không checkout.
python thu_nhanh_leftover.py
python thu_hoi_quy.py
```

Cả hai in **dấu-băm VẬT đang thử** ở dòng đầu, nên phép đo luôn gắn được vào một hệ thống cụ thể
(bài học `he_thong` — ghim THƯỚC là chưa đủ, phải ghim cả VẬT).

---

## Nguyên văn `thu_nhanh_leftover.py` (băm `b2e79bf7bc26`)

```python
#!/usr/bin/env python3
"""Thử nhánh leftover của scripts/submit_log.py — nhánh CHƯA TỪNG CHẠY THẬT.

Chạy submit_log.py THẬT (không chép logic) đối với một server giả, trên một
AI_LOG_DIR giả ở scratchpad. Không đụng .ai-log thật, không đụng repo.

In dấu-băm của chính file đang thử để phép đo gắn được vào một VẬT cụ thể.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path("/Users/soidoc/Code/Projects/P-226")
SCRIPT = REPO / "scripts" / "submit_log.py"
SAN = Path(__file__).parent / "san_thu"

nhan_duoc = []


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(n)
        nhan_duoc.append(json.loads(body.decode()))
        self.send_response(202)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


def bam(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def dung_san(so_dong: int, chen_dong_hong: bool) -> Path:
    if SAN.exists():
        shutil.rmtree(SAN)
    SAN.mkdir(parents=True)
    f = SAN / "session.jsonl"
    with open(f, "w", encoding="utf-8") as out:
        for i in range(so_dong):
            if chen_dong_hong and i == 3:
                out.write('{"id": 3, "noi_dung": "dòng HỎNG bị cắt giữa chừn\n')
                continue
            out.write(json.dumps({"id": i, "noi_dung": f"bản ghi tiếng Việt {i}"},
                                 ensure_ascii=False) + "\n")
    return f


def chay(cong: int) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["AI_LOG_SERVER"] = f"http://127.0.0.1:{cong}/submit"
    env["AI_LOG_API_KEY"] = "khoa-gia"
    env["AI_LOG_DIR"] = str(SAN)
    return subprocess.run([sys.executable, str(SCRIPT)], env=env,
                          capture_output=True, text=True, cwd=str(REPO))


def dem_archive() -> list:
    d = SAN / "archive"
    if not d.exists():
        return []
    ra = []
    for p in sorted(d.glob("*.jsonl")):
        ra += [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return ra


def main():
    srv = HTTPServer(("127.0.0.1", 0), H)
    cong = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    print(f"VẬT ĐANG THỬ  submit_log.py  băm={bam(SCRIPT)}")
    print(f"HEAD repo     {subprocess.run(['git','rev-parse','--short','HEAD'],cwd=REPO,capture_output=True,text=True).stdout.strip()}")
    print()

    # ---- Ca 1: 502 dòng SẠCH → nhánh leftover chạy lần đầu ----
    print("== CA 1: 502 dòng sạch, BATCH_LIMIT=500 → nhánh leftover ==")
    dung_san(502, chen_dong_hong=False)
    for luot in (1, 2):
        r = chay(cong)
        print(f"  lượt {luot}: {r.stderr.strip()}")
    arc = dem_archive()
    ids = [json.loads(l)["id"] for l in arc]
    print(f"  archive: {len(arc)} dòng · id duy nhất: {len(set(ids))} · trùng lặp: {len(ids)-len(set(ids))}")
    print(f"  server nhận tổng: {sum(len(b['entries']) for b in nhan_duoc)} bản ghi")
    print(f"  KỲ VỌNG 502/502/0 → {'ĐẠT' if (len(arc),len(set(ids)))==(502,502) else 'TRƯỢT'}")
    print()

    # ---- Ca 2: dòng HỎNG có còn dấu vết ở đâu không? ----
    nhan_duoc.clear()
    print("== CA 2: 10 dòng, 1 dòng JSON HỎNG (bị cắt giữa chừng) ==")
    dung_san(10, chen_dong_hong=True)
    r = chay(cong)
    print(f"  {r.stderr.strip()}")
    arc = dem_archive()
    print(f"  server nhận: {sum(len(b['entries']) for b in nhan_duoc)} bản ghi")
    print(f"  archive:     {len(arc)} dòng")
    print(f"  session.jsonl còn lại: {'CÓ' if (SAN/'session.jsonl').exists() else 'KHÔNG'}")
    con_dau_vet = any("HỎNG" in l for l in arc)
    print(f"  dòng HỎNG còn dấu vết ở archive: {'CÓ' if con_dau_vet else 'KHÔNG — MẤT HẲN'}")

    # ---- Ca 3: thứ tự thời gian khi hook ghi thêm giữa chừng ----
    nhan_duoc.clear()
    print()
    print("== CA 3: 502 dòng cũ + hook ghi 2 dòng MỚI ngay sau khi POST ==")
    dung_san(502, chen_dong_hong=False)
    r = chay(cong)  # lượt 1: gửi 500, leftover 2 ghi về LOG_FILE
    # giả lập hook ghi thêm 2 bản ghi MỚI (id 900, 901) SAU lượt 1
    with open(SAN / "session.jsonl", "a", encoding="utf-8") as f:
        for i in (900, 901):
            f.write(json.dumps({"id": i, "noi_dung": "MỚI"}, ensure_ascii=False) + "\n")
    thu_tu = [json.loads(l)["id"] for l in (SAN/"session.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  thứ tự trong session.jsonl sau lượt 1 + hook: {thu_tu}")
    print(f"  KỲ VỌNG cũ-trước-mới [500, 501, 900, 901] → {'ĐẠT' if thu_tu==[500,501,900,901] else 'TRƯỢT'}")

    srv.shutdown()


if __name__ == "__main__":
    main()
```

---

## Nguyên văn `thu_hoi_quy.py` (băm `301a1d797e55`)

```python
#!/usr/bin/env python3
"""Hai câu hỏi, đo thật:

A. Dòng JSON hỏng MẤT HẲN — là hồi quy do eadcca7, hay vốn đã thế?
   → chạy CÙNG kịch bản trên bản TRƯỚC vá (eadcca7^) và bản SAU vá.

B. Đua thứ-tự: hook ghi bản ghi MỚI trong lúc script đang POST.
   → server giả ngủ 1.5s; luồng phụ ghi vào session.jsonl giữa chừng.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path("/Users/soidoc/Code/Projects/P-226")
HERE = Path(__file__).parent
SAN = HERE / "san_hq"
NGU = 0.0


class H(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        self.rfile.read(n)
        time.sleep(NGU)
        self.send_response(202)
        self.end_headers()
        self.wfile.write(b"{}")

    def log_message(self, *a):
        pass


def bam(p): return hashlib.sha256(p.read_bytes()).hexdigest()[:12]


def lay_ban(rev: str) -> Path:
    """Trích submit_log.py ở một revision ra scratchpad (KHÔNG đụng cây làm việc)."""
    out = HERE / f"submit_log.{rev.replace('^','_truoc')}.py"
    r = subprocess.run(["git", "show", f"{rev}:scripts/submit_log.py"],
                       cwd=REPO, capture_output=True, text=True, check=True)
    out.write_text(r.stdout, encoding="utf-8")
    return out


def dung(so_dong, hong_tai=None):
    if SAN.exists():
        shutil.rmtree(SAN)
    SAN.mkdir(parents=True)
    with open(SAN / "session.jsonl", "w", encoding="utf-8") as o:
        for i in range(so_dong):
            if hong_tai is not None and i == hong_tai:
                o.write('{"id": %d, "x": "dòng HỎNG cắt giữa chừn\n' % i)
                continue
            o.write(json.dumps({"id": i, "x": f"vi {i}"}, ensure_ascii=False) + "\n")


def chay(script: Path, cong: int):
    env = dict(os.environ)
    env.update(AI_LOG_SERVER=f"http://127.0.0.1:{cong}/s",
               AI_LOG_API_KEY="k", AI_LOG_DIR=str(SAN))
    return subprocess.run([sys.executable, str(script)], env=env,
                          capture_output=True, text=True, cwd=str(REPO))


def arc_lines():
    d = SAN / "archive"
    if not d.exists():
        return []
    ra = []
    for p in sorted(d.glob("*.jsonl")):
        ra += [l for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
    return ra


def main():
    global NGU
    srv = HTTPServer(("127.0.0.1", 0), H)
    cong = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    truoc = lay_ban("eadcca7^")
    sau = lay_ban("eadcca7")
    print(f"bản TRƯỚC vá (eadcca7^) băm={bam(truoc)}")
    print(f"bản SAU   vá (eadcca7)  băm={bam(sau)}")
    print(f"bản trên ĐĨA hiện nay   băm={bam(REPO/'scripts'/'submit_log.py')}")
    print()

    print("== A. Dòng JSON hỏng có còn dấu vết trong archive không? ==")
    for ten, s in (("TRƯỚC vá", truoc), ("SAU vá  ", sau)):
        dung(10, hong_tai=3)
        chay(s, cong)
        a = arc_lines()
        con = any("HỎNG" in l for l in a)
        print(f"  {ten}: archive {len(a):2d} dòng · dòng hỏng: "
              f"{'CÒN (truy được)' if con else 'MẤT HẲN'}")
    print()

    print("== B. Đua thứ-tự: hook ghi bản ghi MỚI trong lúc đang POST ==")
    NGU = 1.5
    dung(502)

    def hook_ghi():
        time.sleep(0.6)  # rơi vào giữa lúc POST đang treo
        with open(SAN / "session.jsonl", "a", encoding="utf-8") as f:
            for i in (900, 901):
                f.write(json.dumps({"id": i, "x": "MOI"}, ensure_ascii=False) + "\n")

    t = threading.Thread(target=hook_ghi)
    t.start()
    r = chay(sau, cong)
    t.join()
    print(f"  {r.stderr.strip()}")
    ids = [json.loads(l)["id"] for l in
           (SAN / "session.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    print(f"  thứ tự session.jsonl còn lại: {ids}")
    print(f"  cũ (500,501) đứng TRƯỚC mới (900,901)? "
          f"{'ĐẠT' if ids == [500,501,900,901] else 'TRƯỢT — mới đứng trước cũ'}")
    print(f"  (nhánh THẤT BẠI _restore_pending cố ý xử lý đúng ca này: 'pending (older) + LOG_FILE (newer)')")

    srv.shutdown()


if __name__ == "__main__":
    main()
```
