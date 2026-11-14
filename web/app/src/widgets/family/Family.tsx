"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCurrentCase } from "@/features/cases";
import { useFamily } from "@/features/families";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { FamilyDesktop } from "./FamilyDesktop";
import { FamilyMobile } from "./FamilyMobile";

/** The case file of this browser's family, or the way to open one. */
export function Family() {
  const t = useTranslations("widget.family");
  const errorMessage = useApiErrorMessage();
  const { family, loading, missing, error, retry } = useFamily();
  const { current } = useCurrentCase();
  const isMobile = useIsMobile();

  if (family) {
    return isMobile ? (
      <FamilyMobile family={family} current={current} />
    ) : (
      <FamilyDesktop family={family} current={current} />
    );
  }

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
      ) : (
        <div role="alert" className="mt-10 flex flex-col items-start gap-3">
          <p className="text-body">{errorMessage(error)}</p>
          <TypedButton onClick={() => void retry()}>{t("retry")}</TypedButton>
        </div>
      )}
    </NotebookPage>
  );
}
