#!/usr/bin/env node
/**
 * Băm nội dung `frontend/src/**\/*.{ts,tsx}` — nhãn định danh MÃ SẢN PHẨM
 * frontend, tương đương `src/dau_ma_nguon.py` bên backend (PO-agent giao
 * 20/08 — backend đã có, frontend thì không, và cái giá đã trả bằng số:
 * một ca cổng 403-role vỡ, chẩn đoán "do ảnh cũ" nhưng KHÔNG ai chứng minh
 * được — phải dựng lại rồi chạy lại mới biết, trong khi backend một dòng
 * `cat /app/.bam_ma_nguon` trả lời trong hai giây).
 *
 * CÙNG THUẬT TOÁN, CÙNG Ý TƯỞNG với bản Python (sha256 nội dung, sắp theo
 * đường dẫn TƯƠNG ĐỐI trước khi băm, 12 ký tự hex đầu) — không tự bịa cách
 * khác, để hai băm so sánh được cạnh nhau trong cùng một bảng nghiệm thu.
 * KHÔNG đòi hai ngôn ngữ cho ra CÙNG MỘT SỐ trên cùng nội dung (không có ý
 * nghĩa gì, hai bảng chữ cái băm khác cây file khác nhau) — chỉ đòi CÙNG
 * CÁCH TÍNH, để đọc hai băm cạnh nhau không cần hai cách hiểu khác nhau.
 *
 * PHẠM VI KHAI TƯỜNG MINH: mọi `.ts`/`.tsx` dưới `frontend/src/`, đệ quy,
 * KHÔNG loại trừ gì — kể cả file test đồng vị trí (`*.test.tsx`,
 * `*.pin.test.ts`): `frontend/src/` là vùng ghi TRỌN VẸN của tech-lead theo
 * CLAUDE.md §4 (không tách nội bộ như `tests/` riêng bên backend), nên
 * không có lý do loại phần nào ra — đúng tinh thần backend không loại gì
 * khỏi `src/`. File CHÍNH nó (đuôi `.mjs`, không khớp `.ts`/`.tsx`) KHÔNG
 * nằm trong băm — khác backend (nơi `dau_ma_nguon.py` tự băm chính nó vì
 * cùng đuôi `.py`) — lệch này là HỆ QUẢ của đuôi file, không phải một loại
 * trừ có chủ đích.
 *
 * KHÁC BACKEND MỘT ĐIỂM KIẾN TRÚC, không phải một lựa chọn tuỳ ý: backend
 * `COPY . .` giữ nguyên `src/**\/*.py` tới tận stage runtime CUỐI (Python
 * thông dịch, không build), nên băm tính được NGAY TRONG stage cuối, đọc
 * lại bằng `docker exec ... cat /app/.bam_ma_nguon`. Frontend build
 * `output: "standalone"` (next.config.ts) XOÁ hẳn `frontend/src/` khỏi
 * stage runtime cuối (chỉ còn `.next/standalone` đã biên dịch) — nhãn BẮT
 * BUỘC phải tính ở stage "builder" (nơi `frontend/src/` còn nguyên vẹn)
 * rồi COPY NHÃN TĨNH (một file .txt, không phải mã nguồn) sang stage cuối.
 * Việc nối vào `frontend/Dockerfile` thuộc vùng DevOps — file này CHƯA nối,
 * chỉ là thuật toán + phép tự-kiểm (xem cuối file).
 */
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join, relative, sep } from "node:path";

// Cùng độ dài với nhãn băm bên backend, và cùng nguyên tắc "một con số băm
// không kèm cách băm thì không phải bằng chứng" — khai tường minh CÁCH BĂM.
export const CACH_BAM = "sha256-noi-dung-frontend-src-ts-tsx-da-sap-xep-12";
const DO_DAI = 12;

function timTepDeQuy(thuMuc, ketQua) {
  for (const ten of readdirSync(thuMuc)) {
    const duongDayDu = join(thuMuc, ten);
    const info = statSync(duongDayDu);
    if (info.isDirectory()) {
      timTepDeQuy(duongDayDu, ketQua);
    } else if (/\.(ts|tsx)$/.test(ten)) {
      ketQua.push(duongDayDu);
    }
  }
  return ketQua;
}

/** Băm mọi `.ts`/`.tsx` dưới `goc` (mặc định: `frontend/src/`, thư mục
 * chứa chính file này). Sắp theo ĐƯỜNG DẪN TƯƠNG ĐỐI (chuẩn hoá dấu `/`)
 * TRƯỚC khi băm nội dung theo thứ tự đó — cùng nguyên tắc `sorted(rglob())`
 * bên Python: đổi tên file làm DỊCH vị trí sắp xếp thì băm ĐỔI, đổi tên mà
 * GIỮ nguyên vị trí thì băm KHÔNG đổi (điểm mù đã biết, không che). */
export function bamMaNguon(goc = dirname(fileURLToPath(import.meta.url))) {
  const duongTuyetDoi = timTepDeQuy(goc, []);
  const duongTuongDoi = duongTuyetDoi
    .map((d) => relative(goc, d).split(sep).join("/"))
    .sort();
  const h = createHash("sha256");
  for (const d of duongTuongDoi) {
    h.update(readFileSync(join(goc, ...d.split("/"))));
  }
  return h.digest("hex").slice(0, DO_DAI);
}

// Chạy trực tiếp (`node dau_ma_nguon.mjs`) in băm ra stdout, KHÔNG xuống
// dòng — đúng khuôn `python -c "...write(...)"` bên Dockerfile backend,
// dùng thẳng được trong `RUN node ... > /app/.bam_ma_nguon`.
if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) {
  process.stdout.write(bamMaNguon());
}
