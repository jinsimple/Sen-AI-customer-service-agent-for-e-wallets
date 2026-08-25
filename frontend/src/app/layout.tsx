import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// 🔴 ĐỔI 25/08 — Nunito -> Inter. Không phải chuyện gu.
// Nunito là phông BO TRÒN, thân thiện — đúng cho app trẻ em / học tập. Đây là
// sản phẩm TÀI CHÍNH xử lý khiếu nại tiền, và phông đang nói sai về sản phẩm
// TRƯỚC CẢ KHI người ta đọc nội dung. Inter là grotesque trung tính, gần SF Pro
// của Apple nhất trong số phông miễn phí.
// 🔴 `subsets` PHẢI có "vietnamese": thiếu nó thì đúng những chữ CÓ DẤU âm thầm
// rơi về phông hệ thống — chữ nhảy phông GIỮA CÂU, tệ hơn hẳn giữ Nunito.
// Bỏ weight 800: [ĐO] 9 chỗ dùng, mà đã có 600 và 700 thì 800 không thêm bậc
// nào, chỉ thêm nhiễu.
const inter = Inter({
  variable: "--font-ui",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "600", "700"],
});

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500", "700"],
});

export const metadata: Metadata = {
  title: "Sen — Trợ lý CSKH ví điện tử",
  description: "FIN-05 — AI Agent CSKH xử lý khiếu nại giao dịch ví điện tử",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="vi" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
