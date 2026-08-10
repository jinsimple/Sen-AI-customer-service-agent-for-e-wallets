import type { Metadata } from "next";
import { Nunito, JetBrains_Mono } from "next/font/google";
import "./globals.css";

// Font đúng theo design token "Mận Sen" (FIN05-Wireframe-UXUI.html §Tổng quan):
// Nunito cho UI/hội thoại, JetBrains Mono cho dữ liệu dạng bảng cần căn cột.
const nunito = Nunito({
  variable: "--font-ui",
  subsets: ["latin", "vietnamese"],
  weight: ["400", "600", "700", "800"],
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
    <html lang="vi" className={`${nunito.variable} ${jetbrainsMono.variable}`}>
      <body>{children}</body>
    </html>
  );
}
