import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n/client";
import { getLang, getT } from "@/lib/i18n/server";

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

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getT();
  return { title: t("app.metaTitle"), description: t("app.metaDescription") };
}

export default async function RootLayout({ children }: LayoutProps<"/">) {
  const lang = await getLang();
  return (
    <html lang={lang} className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body>
        <I18nProvider lang={lang}>{children}</I18nProvider>
      </body>
    </html>
  );
}
