# Lưu trữ — §5.C (ĐÍNH CHÍNH 18/08) chuyển từ `docs/STATE.md`

> Dọn theo §7b (Lead thực hiện 20/08, theo yêu cầu PO-agent). Mục đã ĐÓNG (đính chính tự khép,
> không còn quyết định nào treo) — chuyển nguyên văn, để lại một dòng trỏ trong `STATE.md`.

## 🟢 C. ĐÍNH CHÍNH 18/08 — hai phát biểu trong kho tài liệu là SAI, đã kiểm tận mắt

**C1 · "khách đọc lý do từ chối SAI (*vượt 200.000 TPM*)" — SAI. Không có đường nào tới mắt khách.**
Bắt bởi **tech-lead**; PO-agent kiểm lại độc lập trước khi ghi.

```
[ĐO] src/api/main.py:621   là CHÚ THÍCH
[ĐO] src/api/main.py:629-630  chuỗi khách thật sự nhận:
     "Hệ thống đang xử lý nhiều yêu cầu cùng lúc, bạn vui lòng thử lại
      sau khoảng 30 giây giúp mình nhé."          ← KHÔNG số, KHÔNG chữ "TPM"
[ĐO] grep -rn "TPM" src/        → 5 hit, 5/5 là chú thích/docstring
     rate_limit.py:60,62,69 · main.py:379 · main.py:621
[ĐO] grep -rnE "200\.000|200000|200_000" src/  → 3 hit, 3/3 chú thích
     (rate_limit.py:60 viết "200K" — cách viết thứ tư, chỉ lọt lưới nếu grep theo dấu chấm)
[ĐO] grep -rnE "TPM|200\.000" frontend/src/    → 0 hit
```

⟹ **Đổi HẠNG việc, không chỉ đổi chữ:** không phải *"khách đang đọc chữ sai"* (đối ngoại, gấp)
mà là *"căn cứ chết nằm trong chú thích"* (đối nội, không gấp). Nó **là cùng một việc** với sổ nợ
§6.⓸ `_AGENT_MAX_CONCURRENT` mất căn cứ — **không phải việc riêng**, và **không đi cùng đợt ①**
nữa, vì lý do gom nó vào ① chính là cái vừa mất.

> **Vì sao lỗi này sinh ra:** dòng 621 nằm đúng **5 dòng trên** một `detail=` khách-đọc-được. Ai
> `grep "200.000"` sẽ thấy hit ở 621, liếc xuống thấy `HTTPException(detail=…)` ngay dưới, rồi
> ghép hai thứ. **Cùng lớp lỗi với đính chính ADR-031** (grep trúng dòng 143, câu trả lời ở dòng
> 150) và đúng nếp kiểm §8 — *một khung nhìn đã bị chính lệnh grep của mình lọc, rồi dùng như toàn
> cảnh*. Lần này **bộ lọc là KHOẢNG CÁCH 5 DÒNG.**

**C2 · "`test_f31_f32` chưa có cổng chi phí (tester biết, chưa sửa)" — SAI từ lúc viết.**
`scripts/BAN-GIAO-coder-2026-08-17.md` §④ ghi câu đó và dặn *"ĐỪNG chạy `pytest tests/` toàn bộ"*.

```
[ĐO] cổng land ở 07ee30e  17/08 22:41  "cổng chi phí cho test_f31_f32 — lỗ CUỐI trong họ này"
[ĐO] bàn giao viết ở      17/08 22:46  (4ac2162) và commit muộn hơn nữa (3734c2b)
[ĐO] git merge-base --is-ancestor 07ee30e 4ac2162  → ĐÚNG
[ĐO] tests/test_agents/test_f31_f32_duong_agent_that.py:133  skipif(not duoc_phep_ton_tien())
```

🔴 **ĐỪNG đọc thành "vậy chạy `pytest tests/` được rồi".** Cái chết là **LÝ DO**, không phải lệnh
cấm: lệnh cấm còn hai chân khác chưa ai kiểm — bộ test thứ tư chưa khai cổng (§3, mẫu số "3/3 bộ
ĐÃ BIẾT"), và **lớp ② đang mất**. Đây đúng ca Luật B: *một lời dặn KHÔNG hành động cạnh một dữ
kiện ĐẨY hành động thì dữ kiện thắng* — nên nói rõ cả hai vế.
