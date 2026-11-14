"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useConfirmedSubscription } from "@/features/billing";
import { useDetectivesLabel } from "@/features/families";
import { useCurrentCase, useStartNextCaseMutation } from "@/features/cases";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import {
  DetectivesTag,
  HandNote,
  NotebookPage,
  PlansLink,
  StampButton,
  StampLink,
  TypedButton,
  Wordmark,
} from "@/shared/components/notebook";

/** Where Stripe sends the parent back. One column on every screen. */
export function BillingReturn({ outcome }: { outcome: "success" | "cancel" }) {
  const t = useTranslations("widget.billing-return");
  const detectivesLabel = useDetectivesLabel();
  return (
    <NotebookPage>
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col items-start">
          <Wordmark text={t("wordmark")} size="sm" />
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <PlansLink />
      </div>
      <div className="mt-12 flex flex-col gap-6">
        {outcome === "success" ? (
          <Paid />
        ) : (
          <>
            <h1 className="text-title">{t("cancel.title")}</h1>
            <HandNote>{t("cancel.text")}</HandNote>
            <StampLink href="/family">{t("back")}</StampLink>
          </>
        )}
      </div>
    </NotebookPage>
  );
}

function Paid() {
  const t = useTranslations("widget.billing-return");
  const router = useRouter();
  const errorMessage = useApiErrorMessage();
  const { current } = useCurrentCase();
  const subscription = useConfirmedSubscription();
  const [startNext, starting] = useStartNextCaseMutation();
  const next = current?.status === "solved" ? current.number + 1 : null;
  const notYet = starting.error && toApiError(starting.error).code === "billing.payment_required";

  if (!subscription.active) {
    return (
      <div role="status" className="flex flex-col items-start gap-4">
        <h1 className="text-title">{t("confirming.title")}</h1>
        {subscription.error ? (
          <p role="alert" className="font-type text-label text-gentle-error-fg">
            {errorMessage(subscription.error)}
          </p>
        ) : subscription.slow ? (
          <HandNote lead={t("confirming.slowLead")}>{t("confirming.slow")}</HandNote>
        ) : (
          <HandNote>{t("confirming.text")}</HandNote>
        )}
        {subscription.slow || subscription.error ? (
          <TypedButton onClick={() => void subscription.retry()}>{t("confirming.retry")}</TypedButton>
        ) : null}
      </div>
    );
  }

  return (
    <>
      <h1 className="text-title">{t("success.title")}</h1>
      <HandNote>{t("success.text")}</HandNote>
      {next ? (
        <StampButton
          disabled={starting.isLoading}
          onClick={async () => {
            try {
              await startNext().unwrap();
              router.push("/family");
            } catch {
              // shown below
            }
          }}
        >
          {t("success.start", { number: next })}
        </StampButton>
      ) : (
        <StampLink href="/family">{t("back")}</StampLink>
      )}
      {starting.error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {notYet ? t("success.notYet") : errorMessage(starting.error)}
        </p>
      ) : null}
    </>
  );
}
