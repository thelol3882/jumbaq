"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCurrentCase, useStartNextCaseMutation } from "@/features/cases";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, PlansLink, StampButton, StampLink, Wordmark } from "@/shared/components/notebook";

/** Where Stripe sends the parent back. One column on every screen. */
export function BillingReturn({ outcome }: { outcome: "success" | "cancel" }) {
  const t = useTranslations("widget.billing-return");
  return (
    <NotebookPage>
      <div className="flex items-center justify-between gap-4">
        <Wordmark text={t("wordmark")} size="sm" />
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
  const [startNext, starting] = useStartNextCaseMutation();
  const next = current?.status === "solved" ? current.number + 1 : null;
  // Stripe tells the API a moment after it sends the parent back.
  const notYet = starting.error && toApiError(starting.error).code === "billing.payment_required";

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
