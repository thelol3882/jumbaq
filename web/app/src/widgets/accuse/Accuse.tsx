"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { playedCount, useCurrentCase, type Accusation } from "@/features/cases";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { AccuseDesktop } from "./AccuseDesktop";
import { AccuseMobile } from "./AccuseMobile";

/** The accusation after the fifth evening, then the solved case and its certificate. */
export function Accuse({ caseNumber }: { caseNumber: number }) {
  const t = useTranslations("widget.accuse");
  const errorMessage = useApiErrorMessage();
  const isMobile = useIsMobile();
  const { current, loading, error, retry } = useCurrentCase();
  // Right after the last answer the worker still has to move the case to the accusation.
  const almost =
    current?.status === "active" && current.episodes.length > 0 && playedCount(current.episodes) === current.episodes.length;
  // The reveal comes only with the right accusation, so it lives here until the page closes.
  const [solved, setSolved] = useState<Accusation | null>(null);

  if (current && current.number === caseNumber && (current.status === "accusing" || current.status === "solved")) {
    const View = isMobile ? AccuseMobile : AccuseDesktop;
    return <View current={current} solved={solved} onSolved={setSolved} />;
  }

  return (
    <NotebookPage margin>
      <Wordmark text={t("wordmark")} size="sm" />
      <div className="mt-10 flex flex-col gap-6">
        {loading || almost ? (
          <p role="status" className="font-type text-case font-normal text-ink-muted">
            {t("loading")}
          </p>
        ) : error ? (
          <div role="alert" className="flex flex-col items-start gap-3">
            <p className="text-body">{errorMessage(error)}</p>
            <TypedButton onClick={() => void retry()}>{t("retry")}</TypedButton>
          </div>
        ) : (
          <>
            <h1 className="text-title">{t("notYet.title")}</h1>
            <HandNote>{t("notYet.text")}</HandNote>
            <StampLink href="/family">{t("back")}</StampLink>
          </>
        )}
      </div>
    </NotebookPage>
  );
}
