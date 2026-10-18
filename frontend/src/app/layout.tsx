import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { I18nProvider } from "@/lib/i18n/client";
import { getLang, getT } from "@/lib/i18n/server";

// 🔴 CHANGED Aug 25 — Nunito -> Inter. Not a matter of taste.
// Nunito is a ROUNDED, friendly typeface — right for a kids'/learning app. This is a FINANCIAL
// product handling money complaints, and the font was saying the wrong thing about the product
// BEFORE anyone even reads the content. Inter is a neutral grotesque, the closest free font to
// Apple's SF Pro.
// 🔴 `subsets` MUST include "vietnamese": without it, exactly the ACCENTED characters silently fall
// back to the system font — characters jumping typeface MID-SENTENCE, worse than just keeping
// Nunito.
// Dropped weight 800: [measured] 9 places use it, but with 600 and 700 already present, 800 adds no
// extra step, only noise.
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
