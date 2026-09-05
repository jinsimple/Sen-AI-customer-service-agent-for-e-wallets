// ADR-065 polish (05/09, PO bắt qua ảnh chụp buổi quay) — `full_text` đọc từ
// docx qua trích xuất thô: heading MỤC/ĐIỀU thường DÍNH ĐUÔI ngay sau câu
// cuối của mục trước, KHÔNG xuống dòng (vd thật, MoMo_FAQ_Giao_dich.docx:
// "...giao dịch sẽ không thành công.67. Cách rút tiền từ MoMo về ngân hàng
// đã liên kết\n") — hiện thẳng `full_text` vào 1 khối `pre-wrap` làm cả
// trang thành 1 đoạn văn phẳng, mục sau dính đuôi mục trước.
//
// Module này CHỈ tính TOẠ ĐỘ khối (start/end trong CHÍNH `full_text` GỐC,
// không cắt/nối chuỗi) — cố ý không mutate text để offset `highlight` từ
// backend (ADR-065 gốc) vẫn đúng nguyên, không cần tính lại.
export type PolicyDocBlockType = "heading" | "url" | "para" | "blank";

export interface PolicyDocBlock {
  type: PolicyDocBlockType;
  text: string; // đã trim, chỉ dùng để RENDER — toạ độ start/end vẫn trỏ vào full_text GỐC
  start: number;
  end: number;
}

// Dấu câu kết thúc câu, NGAY SAU đó là số-thứ-tự (FAQ "67. " hoặc ToS
// "1.1. ") rồi tới CHỮ HOA — dấu hiệu THẬT của một heading bị dính đuôi
// (không phải số tiền "30.000.000đ", vì dạng đó không có khoảng trắng sau
// dấu chấm cuối cùng). `\p{Lu}` (Unicode uppercase) thay vì liệt kê tay
// từng chữ hoa có dấu tiếng Việt — liệt kê tay dễ sót, `\p{Lu}` đúng với
// MỌI chữ hoa Unicode (Á/Đ/Ơ/Ư... đều thuộc nhóm Lu).
// `(?<!\d)` chặn TỰ KHỚP NHẦM bên trong số nhiều cấp kiểu ToS "1.1." — không
// có nó, regex đọc "1" + "." (giữa) + "1. " làm một heading giả, cắt "1.1."
// làm đôi thành "1." + "1. ...". Dấu câu kết câu THẬT không bao giờ đứng
// ngay sau một chữ số của CHÍNH số thứ tự đó.
const GLUED_HEADING_RE = /(?<!\d)[.!?](\d+(?:\.\d+)*\.\s+)(?=\p{Lu})/gu;
// Heading đã đứng riêng 1 dòng (không cần dính-đuôi) — FAQ "N. câu hỏi",
// ToS "N.N. tên điều khoản". Không phân biệt được với mục con đánh số bên
// trong 1 câu trả lời (chấp nhận — mục con được tô đậm hơi thừa, KHÔNG phải
// lỗi "dính chữ" PO bắt, đổi đánh đổi này lấy quy tắc đơn giản/dễ soát).
const HEADING_LINE_RE = /^\d+(?:\.\d+)*\.\s+\S/;
const URL_LINE_RE = /^https?:\/\//;

export function splitPolicyDocBlocks(fullText: string): PolicyDocBlock[] {
  const boundaries = new Set<number>([0, fullText.length]);
  let idx = fullText.indexOf("\n");
  while (idx !== -1) {
    boundaries.add(idx + 1);
    idx = fullText.indexOf("\n", idx + 1);
  }
  for (const m of fullText.matchAll(GLUED_HEADING_RE)) {
    // m.index trỏ vào dấu câu kết câu — điểm chẻ NGAY SAU dấu đó (đầu số
    // thứ tự), không lấy theo group 1 (offset của group lệch khỏi m.index
    // tuỳ độ dài phần khớp trước nó, dùng m.index + 1 vì dấu câu luôn 1 ký tự).
    boundaries.add(m.index + 1);
  }

  const sorted = [...boundaries].sort((a, b) => a - b);
  const blocks: PolicyDocBlock[] = [];
  for (let i = 0; i < sorted.length - 1; i++) {
    const start = sorted[i];
    const end = sorted[i + 1];
    const trimmed = fullText.slice(start, end).trim();
    let type: PolicyDocBlockType;
    if (!trimmed) type = "blank";
    else if (URL_LINE_RE.test(trimmed)) type = "url";
    else if (HEADING_LINE_RE.test(trimmed)) type = "heading";
    else type = "para";
    blocks.push({ type, text: trimmed, start, end });
  }
  return blocks;
}

/** Khối có giao với [hlStart, hlEnd) hay không — dùng interval overlap
 * chuẩn, không đòi khớp tuyệt đối (offset highlight từ backend tính trên
 * đúng 1 chunk, có thể lệch vài ký tự khỏi ranh giới khối do trim). */
export function blockOverlapsHighlight(block: PolicyDocBlock, hlStart: number, hlEnd: number): boolean {
  return block.end > hlStart && block.start < hlEnd;
}
