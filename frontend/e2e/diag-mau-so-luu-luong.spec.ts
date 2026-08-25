import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

// TẠM THỜI, KHÔNG COMMIT — mẫu số lưu lượng thật, buổi tốn phí 25/08.
// PO duyệt: gõ câu tự nhiên NGOÀI kịch bản, tối đa 20 hội thoại, mỗi hội
// thoại một luồng mới (loginAs riêng). Ghi lại nguyên văn kể cả câu xử lý
// xấu. duong đọc trực tiếp từ usage.jsonl (docker exec), không cần capture
// network ở đây.

const PHONE = "0974000145";

const CAU_TU_NHIEN = [
  "chào shop",
  "cho em hỏi chuyển tiền quốc tế được không ạ",
  "phí rút tiền về ngân hàng là bao nhiêu vậy",
  "tài khoản em bị khóa rồi làm sao mở lại đây",
  "e chuyển nhầm 2tr5 cho đứa bạn hôm qua giờ nó chưa nhận đc, giúp e với",
  "hôm kia em có chuyển một triệu hai mà giờ ko thấy tới nơi",
  "ủa sao tiền trong ví tự nhiên ít đi vậy trời, ai giải thích giúp em",
  "ba em nhờ em hỏi giúp là ổng chuyển ba trăm nghìn cho người ta mà bên kia báo chưa nhận được",
  "trời ơi giúp em với, em mới chuyển nhầm hết tiền học phí của con cho người lạ rồi",
  "can you tell me the fee for international transfer",
  "e ơi cho hỏi cái này xíu, à mà thôi để em hỏi cái khác",
  "hom qua toi co chuyen 500k nhung nguoi nhan noi chua thay, TXN gi do em quen mat roi",
  "cô muốn hỏi là cô già rồi xài app không rành, sao lúc nãy chuyển tiền xong màn hình nó đứng luôn vậy con",
  "tại sao giao dịch của tôi bị từ chối liên tục vậy, tôi có làm gì sai đâu",
  "anh chuyển 15 triệu mua nhà mà giờ bên nhận nói chưa vô, gấp lắm luôn á",
  "làm ơn cho em xin chính sách hoàn tiền khi giao dịch lỗi ạ",
  "em nhận được tin nhắn báo trúng thưởng phải chuyển phí nhận thưởng, có phải lừa đảo không ạ",
  "sao tự nhiên có người lạ chuyển vào ví em 200k nhắn em chuyển trả qua số khác",
  "kiểm tra giúp em giao dịch lúc sáng nay đi ạ",
  "cảm ơn nha, hỏi vui vậy thôi chứ không có gì đâu",
];

test.describe.configure({ mode: "serial" });

for (let i = 0; i < CAU_TU_NHIEN.length; i++) {
  const cau = CAU_TU_NHIEN[i];
  test(`mẫu ${i + 1}/20: ${cau.slice(0, 40)}`, async ({ page }) => {
    test.setTimeout(60_000);
    await loginAs(page, PHONE, "/chat");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill(cau);
    await input.press("Enter");
    // Chờ bong bóng trả lời mới xuất hiện — không cần đọc nội dung ở đây,
    // duong/usage đọc trực tiếp từ usage.jsonl sau khi chạy hết loạt.
    await expect(page.locator(".bubble-bot").last()).toBeVisible({ timeout: 40_000 });
    await page.waitForTimeout(500);
  });
}
