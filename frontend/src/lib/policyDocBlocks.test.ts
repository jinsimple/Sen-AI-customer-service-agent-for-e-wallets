import { describe, expect, it } from "vitest";
import { blockOverlapsHighlight, splitPolicyDocBlocks } from "./policyDocBlocks";

// ADR-065 polish (05/09, PO bắt qua ảnh chụp) — full_text đọc từ docx thô có
// heading DÍNH ĐUÔI câu trước (không xuống dòng). Ca thật đã đo: mục 67
// MoMo_FAQ_Giao_dich.docx dính vào cuối mục 66.

describe("splitPolicyDocBlocks — FAQ (heading dính đuôi + URL theo sau)", () => {
  const sample =
    "Nếu nhỏ hơn, giao dịch sẽ không thành công.67. Cách rút tiền từ MoMo về ngân hàng đã liên kết\n" +
    "https://www.momo.vn/hoi-dap/cach-rut-tien-tu-momo-ve-ngan-hang-da-lien-ket\n" +
    'Bước 1: Từ màn hình chính, chọn "Rút tiền"';

  it("tách mục 67 thành heading RIÊNG, không dính vào câu trước", () => {
    const blocks = splitPolicyDocBlocks(sample);
    const headings = blocks.filter((b) => b.type === "heading");
    expect(headings).toHaveLength(1);
    expect(headings[0].text).toBe("67. Cách rút tiền từ MoMo về ngân hàng đã liên kết");
  });

  it("dòng URL được nhận diện riêng (để CSS làm mờ/nhỏ)", () => {
    const blocks = splitPolicyDocBlocks(sample);
    expect(blocks.some((b) => b.type === "url" && b.text.startsWith("https://"))).toBe(true);
  });

  it("start/end vẫn trỏ đúng vào full_text GỐC (không mutate) — ghép lại đúng nguyên văn", () => {
    const blocks = splitPolicyDocBlocks(sample);
    const rebuilt = blocks.map((b) => sample.slice(b.start, b.end)).join("");
    expect(rebuilt).toBe(sample);
  });
});

describe("splitPolicyDocBlocks — ToS (số nhiều cấp '1.1.', KHÔNG tự khớp nhầm giữa số)", () => {
  const sample =
    "trước khi sử dụng Sản Phẩm/Dịch Vụ.1. Giải thích từ ngữ\n" +
    "1.1. M_Service: là Công Ty Cổ Phần Dịch Vụ Di Động Trực Tuyến.\n" +
    "1.2. Ứng Dụng MoMo: là Ứng dụng trên nền tảng di động.";

  it("KHÔNG cắt đôi '1.1.' thành '1.' + '1. ...' (lỗi tự khớp nhầm đã bắt được)", () => {
    const blocks = splitPolicyDocBlocks(sample);
    expect(blocks.some((b) => b.text === "1.")).toBe(false);
  });

  it("mỗi mục 1. / 1.1. / 1.2. là MỘT heading riêng, đúng nguyên văn", () => {
    const blocks = splitPolicyDocBlocks(sample).filter((b) => b.type === "heading");
    expect(blocks.map((b) => b.text)).toEqual([
      "1. Giải thích từ ngữ",
      "1.1. M_Service: là Công Ty Cổ Phần Dịch Vụ Di Động Trực Tuyến.",
      "1.2. Ứng Dụng MoMo: là Ứng dụng trên nền tảng di động.",
    ]);
  });
});

describe("splitPolicyDocBlocks — không khớp nhầm số tiền", () => {
  it("'30.000.000đ' không có khoảng trắng sau dấu chấm — không bị coi là heading", () => {
    const sample = "Hạn mức tối đa là 30.000.000đ mỗi tháng cho giao dịch này.";
    const blocks = splitPolicyDocBlocks(sample);
    expect(blocks.every((b) => b.type !== "heading")).toBe(true);
  });
});

describe("splitPolicyDocBlocks — tài liệu ngắn (FAQ 1 đoạn, không heading)", () => {
  it("hiện thẳng thành 1 khối, không lỗi", () => {
    const sample = "FAQ ngắn — phí rút tiền là 5.500đ mỗi lần.";
    const blocks = splitPolicyDocBlocks(sample).filter((b) => b.type !== "blank");
    expect(blocks).toHaveLength(1);
    expect(blocks[0].type).toBe("para");
    expect(blocks[0].text).toBe(sample);
  });
});

describe("blockOverlapsHighlight", () => {
  it("khối giao với khoảng tô sáng → true", () => {
    const block = { type: "para" as const, text: "x", start: 10, end: 20 };
    expect(blockOverlapsHighlight(block, 15, 25)).toBe(true);
  });

  it("khối nằm ngoài khoảng tô sáng → false", () => {
    const block = { type: "para" as const, text: "x", start: 10, end: 20 };
    expect(blockOverlapsHighlight(block, 20, 30)).toBe(false);
    expect(blockOverlapsHighlight(block, 0, 10)).toBe(false);
  });
});
