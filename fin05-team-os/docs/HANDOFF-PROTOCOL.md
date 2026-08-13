<!-- check_contracts: ignore — file này chỉ mô tả cơ chế, các hash bên dưới là ví dụ -->

# Giao thức bàn giao giữa các vai

> File này giải quyết đúng một vấn đề: *"Claude tech lead đổi cấu trúc, Claude tester và
> Claude bảo mật không biết."*
>
> Câu trả lời ngắn: **agent không bàn giao cho nhau. Agent bàn giao cho `contracts/`.**

## 1. Vì sao không dùng "file tóm tắt"

Cách làm tự nhiên là bắt tech-lead viết `docs/thay-doi-moi-nhat.md` cho tester đọc. Nó hỏng vì:

| Vấn đề | Hệ quả |
|---|---|
| Tech lead phải **nhớ** viết | Quên một lần là tester làm sai cả buổi |
| Không có cách nào biết tóm tắt đã cũ | Tester đọc file 3 ngày trước và tưởng nó mới |
| Tóm tắt là diễn giải, không phải sự thật | Hai agent hiểu khác nhau về cùng một thay đổi |
| Không ai kiểm được tóm tắt có đầy đủ không | Thiếu sót im lặng — loại lỗi tệ nhất |

Thay vào đó: **một nguồn sự thật + một máy phát hiện lệch.**

## 2. Cơ chế

```
                    ┌──────────────┐
                    │  contracts/  │  ← nguồn sự thật duy nhất
                    └──────┬───────┘
                           │ băm SHA256
                           ▼
              scripts/check_contracts.py
                           │
      ┌────────────────────┼────────────────────┐
      ▼                    ▼                    ▼
   tests/            docs/security/       docs/user-stories/
 CONTRACT_VERSION   CONTRACT_VERSION      CONTRACT_VERSION
      = @abc123         = @abc123             = @abc123
             │
             └─→ hash lệch = STALE = CI đỏ = có người phải làm lại
```

Mỗi artifact hạ nguồn tự khai báo nó được sinh ra từ phiên bản contract nào:

```python
# đầu file test
CONTRACT_VERSION = {"authority-matrix.yaml": "cdc333ce54b3"}
```

```markdown
<!-- đầu file báo cáo -->
<!-- CONTRACT_VERSION: authority-matrix.yaml=cdc333ce54b3 -->
```

Lấy dòng khai báo bằng: `python scripts/check_contracts.py --stamp authority-matrix.yaml`

Không ai phải nhớ báo cho ai nữa. Máy nhắc, và nhắc mỗi lần `/standup`.

## 3. Quy trình đổi contract — bắt buộc

```
tech-lead nhận ra cần đổi cấu trúc
        │
        ├─ DỪNG CODE
        │
        ├─ 1. Sửa file trong contracts/
        ├─ 2. /adr  (ghi rõ VÌ SAO bác bỏ phương án cũ)
        ├─ 3. Hỏi Bách duyệt ── CHỜ ──
        ├─ 4. python scripts/check_contracts.py --update
        │
        └─ 5. Code

sau đó, ở phiên bất kỳ:
   /standup  →  "artifact lỗi thời: tests/test_authority.py"
   /impact   →  "vì transition X đổi ngữ nghĩa, giao lại cho tester"
```

Bước 3 không được bỏ. Nếu tech-lead tự duyệt thay đổi contract, bạn mất lớp HITL của chính
quy trình — và mỉa mai thay, đó đúng là lỗi mà sản phẩm này sinh ra để phòng chống.

## 4. Phân vùng quyền ghi

Hai agent ghi vào cùng một file là nguồn xung đột thầm lặng. Mỗi vùng có đúng một chủ sở hữu.

| Vùng | Chủ sở hữu | Người khác muốn đổi |
|---|---|---|
| `contracts/` | tech-lead | đề xuất → tech-lead thực hiện sau khi Bách duyệt |
| `src/` | tech-lead | đề xuất, không sửa |
| `tests/`, `eval/` | tester | tech-lead **không được** sửa test cho khớp code |
| `docs/user-stories/` | ba | — |
| `docs/security/` | security | — |
| `PRD.md`, `Brief.md` | po | — |
| `CLAUDE.md` | **chỉ Bách** | mọi agent chỉ đọc |
| `docs/DECISIONS.md` | ghi thêm qua `/adr`, Bách duyệt | không sửa mục cũ |
| `docs/STATE.md` | agent cuối cùng làm việc, qua `/wrapup` | ghi đè |

## 5. Định dạng báo cáo cuối nhiệm vụ

Mọi agent kết thúc bằng khối này. Ba dòng, nhưng chúng là thứ giữ hệ thống không trôi:

```
Contract đã đổi: <danh sách file | không có>
Artifact có thể bị ảnh hưởng: <đoán của bạn, để Bách kiểm chéo với /impact>
Cần Bách quyết: <câu hỏi cụ thể có sẵn lựa chọn | không có>
```

## 6. Khi nào cơ chế này KHÔNG che được

Nói thẳng để bạn không tin nhầm vào nó:

- **Thay đổi ngữ nghĩa không đổi cấu trúc.** Đổi ý nghĩa của `pending_bank` mà không sửa file
  → hash không đổi → không ai được cảnh báo. Phòng bằng cách: mọi thay đổi ý nghĩa phải kèm sửa
  mô tả trong contract, dù chỉ một dòng.
- **Thứ chưa có contract.** Prompt của AI agent, cách hành văn xoa dịu khách hàng, nội dung UI —
  hiện chưa được contract hoá. Nếu chúng trở nên quan trọng (với dự án này thì giọng văn *rất*
  quan trọng), hãy tạo `contracts/tone-of-voice.yaml` và đưa vào cùng cơ chế.
- **Người chạy `--update` cho hết đỏ.** Đây là cách phá hỏng toàn bộ hệ thống, và nó rất cám dỗ
  lúc 11 giờ đêm trước ngày demo. Quy tắc: `--update` chỉ chạy ngay sau khi Bách duyệt một ADR,
  không bao giờ chạy vì "để CI xanh".
