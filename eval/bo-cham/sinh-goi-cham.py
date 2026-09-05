import collections
import random

from cases import CASES

SEED = 20260830
random.seed(SEED)

# --- Xáo có ràng buộc: hai ca cùng kịch bản phải cách xa nhau tối đa có thể ---
groups = collections.defaultdict(list)
for c in CASES:
    groups[c["sid"]].append(c)
for g in groups.values():
    random.shuffle(g)

# Xáo ngẫu nhiên + leo đồi: tối đa hoá KHOẢNG CÁCH NHỎ NHẤT giữa hai ca
# cùng kịch bản. Mục tiêu: người chấm không gặp hai bản gần giống nhau liền kề.
def min_gap(seq):
    p = collections.defaultdict(list)
    for i, c in enumerate(seq):
        p[c["sid"]].append(i)
    gs = [b - a for v in p.values() for a, b in zip(v, v[1:])]
    return min(gs) if gs else 999

def score(seq):
    p = collections.defaultdict(list)
    for i, c in enumerate(seq):
        p[c["sid"]].append(i)
    gs = sorted(b - a for v in p.values() for a, b in zip(v, v[1:]))
    return tuple(gs)  # so sánh từ điển: nâng khoảng cách nhỏ nhất trước

best = None
flat = [c for g in groups.values() for c in g]
for _ in range(400):
    seq = flat[:]
    random.shuffle(seq)
    improved = True
    while improved:                      # leo đồi bằng phép đổi chỗ 2 phần tử
        improved = False
        cur = score(seq)
        for i in range(len(seq)):
            for j in range(i + 1, len(seq)):
                if seq[i]["sid"] == seq[j]["sid"]:
                    continue
                seq[i], seq[j] = seq[j], seq[i]
                s = score(seq)
                if s > cur:
                    cur, improved = s, True
                else:
                    seq[i], seq[j] = seq[j], seq[i]
    if best is None or score(seq) > score(best):
        best = seq[:]
order = best

# --- kiểm khoảng cách tối thiểu giữa hai ca cùng kịch bản ---
pos = collections.defaultdict(list)
for i, c in enumerate(order):
    pos[c["sid"]].append(i)
gaps = {k: min(b - a for a, b in zip(v, v[1:])) for k, v in pos.items() if len(v) > 1}
print("Khoảng cách nhỏ nhất giữa hai ca cùng kịch bản:", gaps)
print("Tổng số ca:", len(order))
print("Phân bố k:", {k: len(v) for k, v in sorted(pos.items())})

# ---------------------------------------------------------------- GÓI CHẤM
HEADER = """# Gói chấm NGƯỜI — 28 lượt · bản v2

> **Chấm mù.** File này KHÔNG chứa phán quyết của máy, KHÔNG chứa mã kịch bản,
> và thứ tự đã xáo. Bảng đối chiếu nằm ở file riêng `KHOA-doi-chieu.md` —
> **chỉ mở SAU khi đã điền xong ô cuối cùng.** Mở sớm là hỏng cả gói, và gói này
> chỉ dùng được **một lần**: chấm rồi thì trạng thái mù mất vĩnh viễn.

## Trước khi bắt đầu — đọc hết mục này

1. **Đọc `RUBRIC-cham-nguoi.md` trước.** Không có rubric thì nhãn của lượt chấm
   buổi sáng và buổi chiều sẽ khác nhau, và nhiễu của người chấm sẽ trộn vào
   nhiễu của mô hình — không tách ra được nữa.
2. **Trong gói CÓ ca lặp lại** (cùng một kịch bản, chạy nhiều lần). Đây là chủ ý,
   để đo độ ổn định. Chấm **từng ca như thể lần đầu gặp**; **không lật lại** nhãn
   đã điền, **không sửa** nhãn cũ cho "nhất quán". Nhất quán giả tạo làm phương
   sai đo được thấp hơn sự thật.
3. **Điền theo đúng thứ tự các ô trong khối** — `rang_buoc` trước, `ket_luan`
   **sau cùng**. Thứ tự này có chủ đích: kết luận điền trước sẽ kéo hai ô kia
   theo nó.
4. **Nhãn che PII** (`[PERSON_VN]`, `[ORGANIZATION]`, `[LOCATION]`) trong văn bản
   là do bộ scrub, **có thể dán sai** (đã đo ~12% câu tiếng Việt bị bóp méo).
   **KHÔNG tính đó là lỗi của agent.** Nếu nhãn sai làm câu trả lời không hiểu
   được → `KHONG_CHAC`, ghi lý do "nhãn PII sai".
5. **Ô `[CHƯA ĐIỀN]` ở phần lời khách là CHẶN.** Ca nào còn `[CHƯA ĐIỀN]` thì
   **không chấm** — xem mục "Việc phải làm trước" bên dưới.

## Việc phải làm trước khi chấm (bắt buộc)

20/28 ca trong bản gốc **không có lượt khách**, chỉ có lời agent. Không biết khách
hỏi gì thì `ket_luan` không có nghĩa — nên các ca đó đang để trống chỗ.

**Cách làm đúng:** chạy một script bơm lượt khách từ nguồn eval vào theo `L-id`,
để người chấm không phải tự tra và không vô tình thấy mã kịch bản.
**Nếu điền tay:** điền **toàn bộ 20 ô trong một lượt riêng, KHÔNG đọc phần agent**,
rồi mới quay lại chấm từ đầu.

## Siêu dữ liệu — điền trước khi chấm

```
nguoi_cham        :
ngay_cham         :
commit_sinh_output:
prompt_version    :
model             :
cach_chon_mau     : (lấy từ pool nào · bao nhiêu ca · chọn kiểu gì)
ca_bi_loai        : (bản gốc ghi 30, thực có 28 — 2 ca đâu, vì sao bỏ)
```

## Khối trả lời

```
rang_buoc  : khong | 1 | 2 | 3 | 4 | 5        ← điền TRƯỚC
co_bia     : khong | so_lieu | chinh_sach | nang_luc   ← điền THỨ HAI
ket_luan   : DAT | TRUOT | KHONG_CHAC          ← điền CUỐI CÙNG
ly_do      : một câu — BẮT BUỘC khi TRUOT, KHONG_CHAC, hoặc co_bia != khong
```

`KHONG_CHAC` là lựa chọn hợp lệ, không phải né tránh. Ép nhị phân một ca thật sự
mơ hồ sẽ biến nó thành một nhãn tuỳ hứng, và nhãn tuỳ hứng không phân biệt được
với nhiễu của mô hình.

---
"""

BLOCK = """## L{n:02d}

**Khách:** {khach}

**Agent:** {agent}

```
rang_buoc  :
co_bia     :
ket_luan   :
ly_do      :
```

---
"""

PLACEHOLDER = "[CHƯA ĐIỀN — bơm lượt khách từ nguồn eval trước khi chấm ca này]"

out = [HEADER]
key = ["# KHOÁ ĐỐI CHIẾU — KHÔNG MỞ TRƯỚC KHI CHẤM XONG\n",
       "> Mở file này trước khi điền xong ô cuối cùng là làm hỏng tính mù của cả gói.\n",
       f"> Seed xáo: `{SEED}`\n",
       "\n| L-id | ca trong file gốc | mã kịch bản |",
       "|---|---|---|"]

for i, c in enumerate(order, 1):
    out.append(BLOCK.format(n=i,
                            khach=c["khach"] if c["khach"] else PLACEHOLDER,
                            agent=c["agent"]))
    key.append(f"| L{i:02d} | Ca {c['ca_cu']:02d} | `{c['sid']}` |")

key.append(f"""
## Cách tổng hợp — đọc trước khi tính bất kỳ tỉ lệ nào

**k lệch rất mạnh.** Một kịch bản chiếm 6/28 lượt, tám kịch bản khác chỉ 1 lượt.
Lấy trung bình phẳng trên 28 dòng là để **một kịch bản chiếm 21% trọng số** của
con số cuối.

**Quy tắc bắt buộc — tổng hợp HAI TẦNG:**

1. **Tầng kịch bản:** với mỗi mã kịch bản, tính tỉ lệ đạt trên k lượt của nó.
   Kịch bản có k ≥ 2 mà **các lượt không đồng nhất** → đánh dấu `KHÔNG ỔN ĐỊNH`
   và báo cáo riêng. Đây là phát hiện có giá trị nhất trong cả gói, đừng để nó
   tan vào một con số trung bình.
2. **Tầng gói:** trung bình **các tỉ lệ ở tầng 1**, mỗi kịch bản một phiếu —
   KHÔNG trung bình 28 dòng.

**`KHONG_CHAC` báo cáo riêng, KHÔNG nằm trong mẫu số** của tỉ lệ đạt. Gộp vào
`TRUOT` là biến "chưa biết" thành "đã biết là sai".

**Câu khai phạm vi — phải đi kèm mọi lần trích con số này, không có ngoại lệ:**

> *Tỉ lệ đo trên gói {len(order)} lượt chấm, phủ {len(pos)} kịch bản (k không cân, từ 1 đến 6),
> một người chấm, chấm mù. Đây KHÔNG phải tỉ lệ đạt của agent trên tập khiếu nại
> thật.*
""")

open("/mnt/user-data/outputs/goi-cham-NGUOI-v2.md", "w").write("\n".join(out))
open("/mnt/user-data/outputs/KHOA-doi-chieu.md", "w").write("\n".join(key))
print("Đã sinh xong.")
