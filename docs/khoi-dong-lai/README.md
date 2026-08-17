# Bộ khởi động lại đội FIN-05

> Dán từng file `0X-*.md` vào một phiên Claude **mới, trắng**. Mỗi file là một vai.
> Viết ngày 18/08/2026, ngay sau khi PO thật tắt đội cũ để tránh ảo giác do phiên chạy quá lâu.

## Thứ tự bật — có lý do, đừng đảo

```
1. PO-agent   (01)  ← bật TRƯỚC. Nó là nơi điều phối và cấp phát; các vai khác báo cáo về đây
2. tech-lead  (02)  ← có việc nặng nhất đang chờ
3. tester     (03)  ← có hai việc chạy song song không chờ ai
4. security   (04)  ← bật khi cần; có 2 câu đang treo, không chặn ai
```

Bật cả bốn cùng lúc cũng được, nhưng **PO-agent phải là nơi bạn dán các quyết định của mình** —
ba vai kia không được tự quyết thay bạn.

## Cách làm việc đã chứng minh là chạy tốt

- **Bạn (PO thật) dán brief vào từng tab riêng.** Đừng để PO-agent spawn subagent — mỗi vai cần
  log tự quản lý và một cửa sổ riêng để bạn đọc được.
- **Các vai nói chuyện với nhau qua PO-agent**, không nói trực tiếp. PO-agent lọc: chỉ chuyển
  **kết luận và lý lẽ**, không chuyển **nội dung corpus** (giữ tường đọc của tester).
- **Cây làm việc dùng chung** ⟹ mọi lệnh `git` phải có pathspec. Đã gây 3 sự cố.

## Điều quan trọng nhất bạn nên biết trước khi bật

Đội cũ mắc **bảy lỗi cùng một lớp trong một ngày**, ba người: *suy từ một tập dữ liệu đã bị lọc mà
không ai khai bộ lọc*. Không ai cố tình lọc — **tập tự đến đã lọc rồi**, và dấu hiệu duy nhất là
**dữ liệu trông quá gọn**.

Quy trình đã chứng minh chữa được nó: **công bố DỰ BÁO vào git TRƯỚC khi chạm vật.** Chạy 2 lần,
trúng 6/6 và 2/2, một lần trúng tới từng chữ số. Bốn prompt dưới đây đều nhúng quy trình này.

Chi tiết: `docs/STATE.md` §8.

## Tệp bàn giao của đội cũ

```
docs/STATE.md                              ← BẢN ĐỒ CHÍNH, ai cũng đọc, 390 dòng
docs/nhat-ky/2026-08-17-nhat-ky-day-du.md  ← toàn bộ lập luận 17/08, 3.001 dòng, tra khi cần
scripts/BAN-GIAO-coder-2026-08-17.md       ← bàn giao tech-lead (3734c2b)
docs/security/                             ← 20+ hồ sơ security
```
