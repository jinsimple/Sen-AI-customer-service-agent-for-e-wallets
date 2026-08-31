# Phép đo NHIỄU 01/09/2026 — bằng chứng cho kết luận ADR-056

**Câu hỏi phép đo này trả lời:** chạy lại **cùng một bản mã, cùng bộ đề** thì kết quả khác nhau
bao nhiêu? Dự án chưa từng đo — và suốt đêm 31/08 mọi khác biệt giữa hai lượt đều bị mặc định
là *do thay đổi*.

## Ba cột, cùng 75 tình huống

| tệp | bản mã | có cổng CTC1? |
|---|---|---|
| `../benchmark-31aug/*_tung_ca.jsonl` | `9c17c5684c9a` | ❌ — baseline 31/08 |
| `nhieu_cu_tung_ca.jsonl` | `9c17c5684c9a` | ❌ — **chạy lại, cùng mã** |
| `buoc4_ket_qua_tung_ca.jsonl` | `ba8a426b6d9a` | ✅ |

Model `qwen3.8-flash` ở cả ba. `hai_nhom_buoc4.csv` = định nghĩa hai nhóm (29 đích · 46 chứng ·
cột `loi_dataset_huong_tien` đánh dấu 2 ca bộ đề sai hướng đã loại).

## Kết quả

| | nhóm CHỨNG (46) | nhóm ĐÍCH (29) |
|---|---|---|
| Pass — baseline | 46 *(theo định nghĩa chọn)* | 0 *(theo định nghĩa)* |
| Pass — chạy lại cùng mã | 27 | 3 |
| Pass — có cổng | **27** | 6 |
| Có gọi công cụ — chạy lại | 42 | 22 |
| Có gọi công cụ — có cổng | 45 | **29** |

**① Cổng KHÔNG gây hồi quy:** chứng 27 vs 27, **bằng nhau**. "19 ca tụt" là nhiễu.
**② Cổng có tác dụng thật:** đích 22/29 → 29/29.
**③ Tiền đề gốc đổ:** đích chọn vì 0/29 gọi công cụ; chạy lại cùng mã thì **22/29 CÓ gọi**.
**④ Điểm không lên:** đích 3 → 6 (n=29, trong nhiễu).

## 🔴 Đọc rồi hãy trích — một cái bẫy thống kê

*"Baseline 46 Pass → chạy lại 30 Pass trên cùng mã"* trông như bằng chứng **điểm tổng bất ổn**.
**KHÔNG PHẢI.** Hai nhóm được chọn **DỰA TRÊN chính kết quả lượt đầu** ⟹ lượt sau **bắt buộc** kém
đi kể cả khi không có nhiễu nào. Đó là **hồi quy về trung bình**.

⟹ **Vẫn CHƯA biết điểm tổng 120 ca dao động bao nhiêu.** Phép đo này không trả lời được — mẫu
thiên lệch. Không nói nó ổn định, cũng không nói nó bất ổn.
⟹ Muốn biết: chạy lại **TOÀN BỘ** golden 120 trên cùng mã, **không chọn lọc**. Chưa làm.

Chi tiết: `docs/DECISIONS.md` ADR-056 (kết luận 01/09) · `docs/STATE.md §0b.20`.
