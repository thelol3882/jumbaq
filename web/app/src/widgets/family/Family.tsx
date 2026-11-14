"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { FamilySummary, useFamily } from "@/features/families";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";

/** The case file of this browser's family, or the way to open one. */
export function Family() {
  const t = useTranslations("widget.family");
  const errorMessage = useApiErrorMessage();
  const { family, loading, missing, error, retry } = useFamily();

  return (
    <NotebookPage margin>
      <Link href="/" className="self-start">
        <Wordmark text={t("wordmark")} size="sm" />
      </Link>
      {loading ? (
        <p role="status" className="mt-10 font-type text-case font-normal text-ink-muted">
          {t("loading")}
        </p>
      ) : missing ? (
        <div className="mt-10 flex flex-col gap-6">
          <h1 className="text-title">{t("missing.title")}</h1>
          <HandNote>{t("missing.note")}</HandNote>
          <StampLink href="/setup">{t("missing.start")}</StampLink>
        </div>
      ) : family ? (
        <div className="mt-8 flex flex-col gap-8">
          <div>
            <p className="font-type text-case">{t("eyebrow")}</p>
            <h1 className="mt-2 text-title">{t("title")}</h1>
          </div>
          <FamilySummary family={family} />
          <HandNote lead={t("next.lead")}>{t("next.text")}</HandNote>
        </div>
      ) : (
        <div role="alert" className="mt-10 flex flex-col items-start gap-3">
          <p className="text-body">{errorMessage(error)}</p>
          <TypedButton onClick={() => void retry()}>{t("retry")}</TypedButton>
        </div>
      )}
    </NotebookPage>
  );
}
