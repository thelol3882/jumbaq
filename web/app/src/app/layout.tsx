import type { Metadata, Viewport } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getTranslations } from "next-intl/server";
import { Providers } from "@/providers";
import { fontVariables } from "@/shared/config/fonts";
import "./globals.css";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("common");
  return {
    title: t("metadata.title"),
    description: t("metadata.description"),
    openGraph: { title: t("metadata.title"), description: t("metadata.description"), type: "website" },
  };
}

export const viewport: Viewport = { themeColor: "#F4F3EC" };

export default async function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang={await getLocale()} className={fontVariables}>
      <body>
        <NextIntlClientProvider>
          <Providers>{children}</Providers>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
