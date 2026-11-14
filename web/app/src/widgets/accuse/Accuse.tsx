"use client";

import { useTranslations } from "next-intl";
import { useState } from "react";
import { playedCount, useCurrentCase, useGetCertificateQuery, type Accusation } from "@/features/cases";
import { useDetectivesLabel } from "@/features/families";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { DetectivesTag, HandNote, NotebookPage, PlansLink, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { AccuseDesktop } from "./AccuseDesktop";
import { AccuseMobile } from "./AccuseMobile";

/** The accusation after the fifth evening, then the solved case and its certificate. */
export function Accuse({ caseNumber }: { caseNumber: number }) {
  const t = useTranslations("widget.accuse");
  const errorMessage = useApiErrorMessage();
  const isMobile = useIsMobile();
  const detectivesLabel = useDetectivesLabel();
  const { current, loading, error, slow, retry } = useCurrentCase();
  // Right after the last answer the worker still has to move the case to the accusation.
  const almost =
    current?.status === "active" && current.episodes.length > 0 && playedCount(current.episodes) === current.episodes.length;
  // The reveal comes only with the right accusation, so it lives here until the page closes.
  const [solved, setSolved] = useState<Accusation | null>(null);
  // The certificate is only asked for once this page shows the solved case.
  const showsSolved = current?.number === caseNumber && current.status === "solved";
  const certificate = useGetCertificateQuery(current?.id ?? "", { skip: !showsSolved });
  const noFamily = error !== undefined && toApiError(error).code === "family.no_session";

  if (current && current.number === caseNumber && (current.status === "accusing" || current.status === "solved")) {
    const View = isMobile ? AccuseMobile : AccuseDesktop;
    return <View current={current} solved={solved} onSolved={setSolved} detectivesLabel={detectivesLabel} certificate={certificate.data} />;
  }

  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col items-start">
          <Wordmark text={t("wordmark")} size="sm" />
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <PlansLink />
      </div>
      <div className="mt-10 flex flex-col gap-6">
        {almost && slow ? (
          <div role="status" className="flex flex-col items-start gap-2">
            <HandNote lead={t("slow.lead")}>{t("slow.text")}</HandNote>
            <TypedButton onClick={() => void retry()}>{t("retry")}</TypedButton>
          </div>
        ) : loading || almost ? (
          <p role="status" className="font-type text-case font-normal text-ink-muted">
            {t("loading")}
          </p>
        ) : noFamily ? (
          <>
            <h1 className="text-title">{t("noFamily.title")}</h1>
            <HandNote>{t("noFamily.note")}</HandNote>
            <StampLink href="/setup">{t("noFamily.start")}</StampLink>
          </>
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
