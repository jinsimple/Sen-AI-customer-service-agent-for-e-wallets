---
description: Ghi một quyết định vào docs/DECISIONS.md — dùng NGAY khi chốt điều gì, đừng để sau
argument-hint: <nội dung quyết định vừa chốt>
allowed-tools: Read, Edit, Bash
---

Ghi ADR cho quyết định: $ARGUMENTS

1. Đọc `docs/DECISIONS.md`, lấy số ADR kế tiếp.
2. Kiểm tra xem có ADR nào trước đây **mâu thuẫn** với quyết định mới không.
   Nếu có → nêu rõ ADR đó và ghi vào mục "Thay thế".
3. **Chỉ ghi thêm vào cuối file.** Không sửa, không xoá ADR cũ. Nếu quyết định mới đảo ngược
   quyết định cũ, ADR cũ vẫn giữ nguyên và ADR mới ghi rõ nó thay thế cái nào.
4. Dùng khuôn sau, giữ ngắn — 10 dòng là đủ:

```markdown
## ADR-0xx — <tên ngắn>
- **Ngày:** <YYYY-MM-DD>
- **Bối cảnh:** <vì sao phải quyết, 1–2 câu>
- **Quyết định:** <chốt cái gì, 1 câu dứt khoát>
- **Phương án đã cân nhắc và bác bỏ:** <cái gì, và **vì sao bác bỏ** — mục này quan trọng nhất,
  nó là thứ chặn agent tương lai "tối ưu" ngược lại>
- **Hệ quả:** <ảnh hưởng tới contract/US/test nào>
- **Thay thế:** <ADR-0xx, hoặc "không">
- **Người duyệt:** PO
```

5. Nếu quyết định này làm đổi file trong `contracts/`, nhắc chạy `python scripts/check_contracts.py --update`.
