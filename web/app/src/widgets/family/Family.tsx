"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useGetSubscriptionQuery } from "@/features/billing";
import { inOpening, tonight, useCurrentCase } from "@/features/cases";
import { useDetectivesLabel, useFamily } from "@/features/families";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, PlansLink, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { useRefetchAt } from "@/shared/hooks/useRefetchAt";
import { FamilyDesktop } from "./FamilyDesktop";
import { FamilyMobile } from "./FamilyMobile";

/** The case file of this browser's family, or the way to open one. */
export function Family() {
  const t = useTranslations("widget.family");
  const errorMessage = useApiErrorMessage();
  const { family, loading, missing, error, retry } = useFamily();
  const detectivesLabel = useDetectivesLabel();
  const { current, slow, error: caseError, retry: check } = useCurrentCase({ skip: !family });
  const subscription = useGetSubscriptionQuery(undefined, { skip: !family });
  const isMobile = useIsMobile();
  const step = current && !inOpening(current) ? tonight(current, new Date()) : undefined;
  useRefetchAt(step?.kind === "waits" ? step.opensAt : null, check);

  if (family) {
    const subscribed = subscription.data?.active ?? false;
    const cancelsAt = subscription.data?.cancels_at ?? null;
    const waiting = { slow, onCheck: () => void check() };
    // A failed poll keeps the case it already has on screen; only a case that never loaded is an error.
    const problem =
      caseError && !current ? (
        <div role="alert" className="flex flex-col items-start gap-3">
          <p className="text-body">{errorMessage(caseError)}</p>
          <TypedButton onClick={() => void check()}>{t("retry")}</TypedButton>
        </div>
      ) : undefined;
    return isMobile ? (
      <FamilyMobile family={family} detectivesLabel={detectivesLabel} current={current} waiting={waiting} problem={problem} subscribed={subscribed} cancelsAt={cancelsAt} />
    ) : (
      <FamilyDesktop family={family} detectivesLabel={detectivesLabel} current={current} waiting={waiting} problem={problem} subscribed={subscribed} cancelsAt={cancelsAt} />
    );
  }

  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        <PlansLink />
      </div>
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
