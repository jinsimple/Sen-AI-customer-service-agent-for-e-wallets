# FIN-05 Team-OS — cài trong 10 phút

Bộ khung vận hành Claude như một đội hoàn chỉnh cho dự án FIN-05, khi bạn làm một mình.

Đọc `FIN05-Team-OS-Chien-luoc.md` để hiểu **vì sao** thiết kế như vậy.
File này chỉ nói **làm thế nào**.

---

## Cài đặt

```bash
# 1. Chép vào repo P-121 (giữ nguyên cấu trúc thư mục)
cp -r fin05-team-os/.claude       /đường/dẫn/P-121/
cp -r fin05-team-os/contracts     /đường/dẫn/P-121/
cp -r fin05-team-os/scripts       /đường/dẫn/P-121/
cp -r fin05-team-os/tests         /đường/dẫn/P-121/
cp -r fin05-team-os/docs          /đường/dẫn/P-121/
cp    fin05-team-os/CLAUDE.md     /đường/dẫn/P-121/

cd /đường/dẫn/P-121

# 2. Cài phụ thuộc
pip install pytest pyyaml

# 3. Chốt baseline lần đầu
python scripts/check_contracts.py --update

# 4. Kiểm tra
pytest tests/test_invariants.py -v
python scripts/check_contracts.py
```

Kỳ vọng: 13 test pass, 4 skip (skip vì `src/` chưa có — chúng tự bật khi bạn bắt đầu code),
`check_contracts.py` báo "Không có artifact lỗi thời".

> Nếu repo đã có `CLAUDE.md`, đừng ghi đè — trộn tay, và giữ trần **200 dòng**.
> File này bị nạp vào mọi phiên; nó phình ra là các agent bắt đầu lơ nó.

---

## Sáu vai

| Gọi bằng | Vai | Dùng khi |
|---|---|---|
| `@po` | Product Owner | Phân tích bài toán, viết/sửa PRD, ưu tiên hoá, xử lý phản hồi demo |
| `@ba` | Business Analyst | Viết User Story + AC, mô hình hoá quy trình, rà độ phủ 12 ô |
| `@tech-lead` | Tech Lead | Thiết kế kỹ thuật, code, sửa contract (**agent duy nhất** được ghi `src/` và `contracts/`) |
| `@tester` | Tester | Viết testcase, chấm eval — **cố ý bị chặn không cho đọc `src/`** |
| `@security` | Bảo mật & tuân thủ | Rà thẩm quyền, PDPA, chuỗi tấn công, đối chiếu NĐ 52/2024 · TT 40/2024 |
| `@critic` | Phản biện | Tìm lý do thiết kế này SAI. Chạy trước mỗi mốc quan trọng |

Vì sao tester không được đọc code: nếu đọc, test sẽ **phản chiếu** logic đang có, kể cả logic sai.
Bạn nhận được một suite xanh mướt chứng minh rằng bug hoạt động đúng như bug.

---

## Năm lệnh

| Lệnh | Khi nào | Mất bao lâu |
|---|---|---|
| `/standup` | Đầu mỗi phiên | ~1 phút |
| `/gate <agent>` | Trước khi giao việc cho một agent | ~1 phút |
| `/adr <quyết định>` | **Ngay khi** chốt điều gì | ~30 giây |
| `/impact` | Sau khi contract đổi, và mỗi cuối tuần | ~2 phút |
| `/wrapup` | Cuối mỗi phiên — **đừng bỏ** | ~3 phút |

`/wrapup` là bước chống mất ngữ cảnh. Bỏ nó một lần thì phiên sau bạn lại phải kể lại từ đầu.

---

## Quy tắc quan trọng nhất

**Đổi cấu trúc = đổi contract TRƯỚC, code SAU.**

```
1. Dừng code
2. Sửa file trong contracts/
3. /adr
4. Hỏi Bách duyệt — CHỜ
5. python scripts/check_contracts.py --update
6. Code
```

Đây là toàn bộ lời giải cho vấn đề *"tech lead đổi cấu trúc mà tester và security không biết"*.
Chi tiết: `docs/HANDOFF-PROTOCOL.md`.

---

## Một ngày điển hình

```
/standup                                    # nạp ngữ cảnh, xem có gì stale
/gate tech-lead "làm US-007 duyệt hoàn tiền" # kiểm input đủ chưa
@tech-lead làm US-007                        # 1 phiên = 1 nhiệm vụ
/gate tester "viết test US-007"
@tester viết test cho US-007                 # phiên riêng, mù code
/wrapup                                      # chốt ngữ cảnh vào repo
```

Cuối tuần thêm: `/impact` và `@critic rà soát toàn bộ trước demo`.

---

## Nội dung gói

```
FIN05-Team-OS-Chien-luoc.md   ← đọc cái này trước
README.md                     ← file này
CLAUDE.md                     ← hiến pháp, nạp vào mọi phiên, trần 200 dòng
.claude/agents/               ← 6 vai
.claude/commands/             ← 5 lệnh
contracts/                    ← nguồn sự thật (3 file có sẵn, 2 file cần tech-lead sinh)
docs/DECISIONS.md             ← ADR, đã mồi 5 mục từ PRD §4 — cần điền ngày thật
docs/STATE.md                 ← trạng thái, ghi đè mỗi /wrapup
docs/HANDOFF-PROTOCOL.md      ← cơ chế bàn giao, đọc kỹ mục 6 (giới hạn)
scripts/check_contracts.py    ← máy phát hiện lệch
tests/test_invariants.py      ← 5 ràng buộc cứng dạng test, chạy được ngay
```

---

## Ba việc nên làm trong ngày đầu

1. **Điền ngày thật vào `docs/DECISIONS.md`** và rà lại mục *"phương án đã cân nhắc và bác bỏ"*
   của từng ADR. Đây là phần có giá trị nhất — nó chặn agent tương lai "tối ưu" ngược lại
   những quyết định bạn đã cân nhắc kỹ (ví dụ điển hình: để CSKH tự duyệt case nội bộ ví).
2. **Cho `@tech-lead` sinh `contracts/fraud-signals.yaml`** từ PRD §5. Mọi ngưỡng chưa được
   chuyên gia xác nhận phải nằm trong mục `open_questions`, không được lẫn vào phần quy định
   như thể đã chắc chắn.
3. **Đưa vào CI** — GitHub Actions chạy `pytest tests/test_invariants.py` và
   `python scripts/check_contracts.py` mỗi push. Không có CI thì cơ chế này chỉ chạy khi
   bạn nhớ chạy, và bạn sẽ quên đúng vào tuần bận nhất.

---

## Cảnh báo

`python scripts/check_contracts.py --update` **chỉ** được chạy ngay sau khi bạn duyệt một ADR.
Không bao giờ chạy nó để "cho CI hết đỏ". Đỏ nghĩa là có artifact thật sự cần làm lại — chạy
`--update` để dập đỏ là cách nhanh nhất phá hỏng toàn bộ hệ thống này, và nó sẽ rất cám dỗ
lúc 11 giờ đêm trước ngày demo.
