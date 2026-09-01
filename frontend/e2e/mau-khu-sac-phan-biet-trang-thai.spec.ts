import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * [ĐO 27/08] Phát hiện thật khi dựng dụng cụ đo màu pixel (không phải diễn
 * tập) — Lead yêu cầu land thành cổng thường trực (Luật A vế bốn: dụng cụ
 * vừa chứng minh mang thông tin bằng cách bắt được một ca hỏng thật).
 *
 * axe-core (contrast) chỉ so CHỮ với NỀN CỦA CHÍNH NÓ — không bao giờ so
 * hai trạng thái KHÁC NHAU với nhau. Trục đó mù hoàn toàn trước cổng này.
 *
 * Đo bằng CSS `filter: grayscale(100%)` THẬT (không tự mô phỏng công thức),
 * lấy màu chữ mỗi status-dot/badge SAU khi khử màu, so sánh trong CÙNG một
 * cột bảng (`data-label` — sự thật cấu trúc DOM, không phải suy từ ý nghĩa
 * nghiệp vụ nằm trong `src/`).
 *
 * 🔴 [ĐO THẬT 27/08, dark mode /dashboard] "Khẩn cấp" (ưu tiên khẩn cấp/nghi
 * gian lận) và "Đã duyệt" (đã xử lý xong) — HAI Ý NGHĨA ĐỐI LẬP trên đúng
 * màn xử lý tiền/gian lận — trùng CHÍNH XÁC một mức xám (khoảng cách 0.0).
 * Một người quét nhanh hàng chờ bằng mắt trên màn hình chỉnh grayscale hoặc
 * bản in đen trắng không phân biệt được hai trạng thái này chỉ bằng màu.
 *
 * VÌ SAO CHỈ SO TRONG CÙNG CỘT, KHÔNG SO TOÀN BỘ TRANG: cột "Phạm vi" cố ý
 * dùng CHUNG một kiểu (`badge-neutral`) cho cả 3 giá trị — không hề định
 * phân biệt bằng màu, chữ là kênh duy nhất NGAY TỪ THIẾT KẾ, không phải lỗi.
 * So sánh CHÉO CỘT (vd "Nội bộ ví" ở cột Phạm vi với "Bình thường" ở cột Ưu
 * tiên) là so hai thứ KHÔNG BAO GIỜ đứng cạnh nhau trong mắt người đọc thật
 * — báo động giả. `data-label` là sự thật CẤU TRÚC (thấy được từ DOM/rendered
 * HTML), tách theo đó không phải suy đoán ý nghĩa nghiệp vụ trong `src/`.
 *
 * VÌ SAO CHỈ SO CẶP KHÁC CLASS: trong CÙNG MỘT CỘT, một cột toàn className
 * giống hệt nhau (như "Phạm vi") nghĩa là bản thân thiết kế CHƯA TỪNG cố
 * phân biệt bằng màu ở đó — không phải hồi quy, không đáng báo. Chỉ đáng
 * báo khi hai class KHÁC NHAU (ý đồ thiết kế là hai màu khác nhau) lại render
 * ra CÙNG một mức xám (ý đồ đó thất bại trên thực tế).
 *
 * Ngưỡng "trùng" đặt Ở MỨC TỐI THIỂU CÓ THỂ BIỆN MINH: < 3 (chừa sai số làm
 * tròn/khử răng cưa) — KHÔNG đặt ngưỡng "phải cách nhau bao nhiêu mới đủ
 * đẹp" (PO đã chỉ rõ: khoảng-cách-RGB không phải thứ mắt cảm nhận, ghim
 * ngưỡng thẩm mỹ là cổng trôi theo bảng màu). "Trùng gần tuyệt đối" là lỗi
 * logic, không phải lựa chọn thiết kế cần bàn.
 *
 * Chọn màu thay thế là việc UX/UI, không phải việc đo — cổng này chỉ bắt
 * SỰ TRÙNG, không đề xuất màu nào nên đổi thành màu nào.
 */

const CSKH_PHONE = "0353000201";
const SUPERVISOR_PHONE = "0905000205";
const NGUONG_TRUNG_GAN_TUYET_DOI = 3;

type MauKhuSac = { text: string; className: string; cot: string; fg: [number, number, number] };

function doSang(rgb: [number, number, number]): number {
  return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
}

async function layMauKhuSacTheoCot(page: import("@playwright/test").Page, selector: string): Promise<MauKhuSac[]> {
  const elements = await page.locator(selector).all();
  const results: MauKhuSac[] = [];
  for (const el of elements) {
    const box = await el.boundingBox();
    if (!box || box.width < 1 || box.height < 1) continue;
    const text = (await el.innerText()).trim();
    if (!text) continue;
    const { className, cot } = await el.evaluate((node) => {
      let p: HTMLElement | null = node as HTMLElement;
      let cot = "(không rõ cột)";
      while (p) {
        const label = p.getAttribute?.("data-label");
        if (label) {
          cot = label;
          break;
        }
        p = p.parentElement;
      }
      return { className: (node as HTMLElement).className, cot };
    });
    const buf = await el.screenshot();
    const b64 = buf.toString("base64");
    const fg = await page.evaluate(async (dataUrl) => {
      const img = new Image();
      img.src = dataUrl;
      await img.decode();
      const canvas = document.createElement("canvas");
      canvas.width = img.width;
      canvas.height = img.height;
      const ctx = canvas.getContext("2d")!;
      ctx.drawImage(img, 0, 0);
      const data = ctx.getImageData(0, 0, img.width, img.height).data;
      const counts = new Map<string, number>();
      for (let i = 0; i < data.length; i += 4) {
        if (data[i + 3] < 200) continue;
        const key = `${data[i]},${data[i + 1]},${data[i + 2]}`;
        counts.set(key, (counts.get(key) || 0) + 1);
      }
      let bgKey: string | null = null;
      let bgCount = -1;
      for (const [k, c] of counts) {
        if (c > bgCount) {
          bgCount = c;
          bgKey = k;
        }
      }
      const bg = bgKey!.split(",").map(Number);
      let best: number[] | null = null;
      let bestDist = -1;
      for (let i = 0; i < data.length; i += 4) {
        const r = data[i],
          g = data[i + 1],
          b = data[i + 2],
          a = data[i + 3];
        if (a < 200) continue;
        const d = Math.sqrt((bg[0] - r) ** 2 + (bg[1] - g) ** 2 + (bg[2] - b) ** 2);
        if (d > bestDist) {
          bestDist = d;
          best = [r, g, b];
        }
      }
      return best as [number, number, number];
    }, `data:image/png;base64,${b64}`);
    results.push({ text, className, cot, fg });
  }
  const seen = new Set<string>();
  return results.filter((r) => (seen.has(r.cot + "|" + r.text) ? false : (seen.add(r.cot + "|" + r.text), true)));
}

async function khongTrungMucXamTrongCungCot(
  page: import("@playwright/test").Page,
  selector: string,
  trang: string
) {
  await page.addStyleTag({ content: "html { filter: grayscale(100%) !important; }" });
  await page.waitForTimeout(300);
  const states = await layMauKhuSacTheoCot(page, selector);
  expect(states.length, `${trang}: 0 trạng thái tìm thấy với "${selector}" — nghi selector sai`).toBeGreaterThan(0);

  const theoCot = new Map<string, MauKhuSac[]>();
  for (const s of states) {
    if (!theoCot.has(s.cot)) theoCot.set(s.cot, []);
    theoCot.get(s.cot)!.push(s);
  }

  let soCapDaXet = 0;
  for (const [cot, nhom] of theoCot) {
    for (let i = 0; i < nhom.length; i++) {
      for (let j = i + 1; j < nhom.length; j++) {
        if (nhom[i].className === nhom[j].className) continue; // cùng class = chưa từng định phân biệt bằng màu
        soCapDaXet++;
        const d = Math.abs(doSang(nhom[i].fg) - doSang(nhom[j].fg));
        expect(
          d,
          `${trang}, cột "${cot}": "${nhom[i].text}" và "${nhom[j].text}" — hai trạng thái KHÁC Ý NGHĨA ` +
            `(class khác nhau: "${nhom[i].className}" vs "${nhom[j].className}") — trùng GẦN NHƯ TUYỆT ĐỐI ` +
            `(${d.toFixed(1)}) sau khi khử màu (grayscale). Người quét nhanh bằng mắt trên màn grayscale/bản ` +
            `in đen trắng không phân biệt được hai trạng thái này chỉ bằng màu.`
        ).toBeGreaterThanOrEqual(NGUONG_TRUNG_GAN_TUYET_DOI);
      }
    }
  }
  expect(soCapDaXet, `${trang}: 0 cặp khác-class trong cùng cột để so — nghi vấn cấu trúc trang đã đổi`).toBeGreaterThan(0);
}

test.describe("KHỬ MÀU — trạng thái KHÁC ý nghĩa (cùng cột) không được trùng mức xám gần tuyệt đối", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`hàng chờ CSKH (/dashboard, ${theme}) — không trạng thái nào trùng xám trong cùng cột`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme });
      await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");
      await page.locator("tbody tr").first().waitFor({ state: "visible", timeout: 15_000 });
      await khongTrungMucXamTrongCungCot(page, ".status-dot, .badge", `/dashboard (${theme})`);
    });

    // Nhật ký duyệt (/approve) KHÔNG dùng bảng có data-label — mọi badge ở
    // đây (Duyệt/Từ chối) đều CÙNG một trục ý nghĩa (kết quả phê duyệt), nên
    // không cần tách cột: hàm dùng chung ở trên tự gộp về một nhóm khi không
    // tìm thấy data-label nào trong chuỗi ancestor — đúng hành vi cần ở đây.
    test(`nhật ký duyệt (/approve, ${theme}) — Duyệt/Từ chối không trùng xám`, async ({ page }) => {
      await page.emulateMedia({ colorScheme: theme });
      await loginAs(page, SUPERVISOR_PHONE, "/approve", 1, "/dang-nhap-noi-bo");
      await page.waitForTimeout(2_000); // dữ liệu nạp bất đồng bộ sau khi mount
      const coDuyet = (await page.locator(".badge-success").count()) > 0;
      const coTuChoi = (await page.locator(".badge-danger").count()) > 0;
      if (!coDuyet || !coTuChoi) {
        test.skip(true, "Nhật ký chưa có đủ cả hai trạng thái Duyệt/Từ chối trên ngăn này — không có gì để so.");
      }
      await khongTrungMucXamTrongCungCot(page, ".badge-success, .badge-danger", `/approve (${theme})`);
    });
  }
});
