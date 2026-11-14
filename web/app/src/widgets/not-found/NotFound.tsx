"use client";

import { useTranslations } from "next-intl";
import { HandNote, NotebookPage, StampLink, Wordmark } from "@/shared/components/notebook";

export function NotFound() {
  const t = useTranslations("widget.not-found");
  return (
    <NotebookPage>
      <Wordmark text={t("wordmark")} size="sm" />
      <p className="mt-10 font-type text-case text-accent-red">{t("eyebrow")}</p>
      <h1 className="mt-2 text-title">{t("title")}</h1>
      <HandNote className="mt-4">{t("text")}</HandNote>
      <div className="min-h-8 grow" />
      <StampLink href="/">{t("home")}</StampLink>
    </NotebookPage>
  );
}
