"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { ManageSubscription, useCheckout, useGetSubscriptionQuery } from "@/features/billing";
import { useDetectivesLabel, useFamily, useStartHref } from "@/features/families";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { DetectivesTag, HandNote, NotebookPage, StampButton, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";

/** The price, the way to pay and the way to cancel. Open to a visitor with no family. One column on every screen. */
export function Plans() {
  const t = useTranslations("widget.plans");
  const errorMessage = useApiErrorMessage();
  const startHref = useStartHref();
  // A visitor without the hint makes no API call, as on the landing page.
  const hinted = startHref !== "/setup";
  const { family, missing, error, retry } = useFamily({ skip: !hinted });
  const subscription = useGetSubscriptionQuery(undefined, { skip: !family });
  const detectivesLabel = useDetectivesLabel();
  const { checkout, redirecting, error: checkoutError } = useCheckout();
  const subscribed = subscription.data?.active === true;
  const anonymous = !hinted || missing;

  return (
    <NotebookPage margin>
      <div className="flex flex-col items-start">
        <Link href="/">
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
      </div>
      <h1 className="mt-8 text-title">{t("title")}</h1>
      <ul className="mt-6 flex flex-col gap-3">
        <li className="text-body">{t("free")}</li>
        <li className="text-body">{t("paid")}</li>
        <li className="font-type text-case font-normal text-ink-muted">{t("cancel")}</li>
      </ul>

      <div className="mt-8 flex flex-col gap-4">
        {anonymous ? (
          <StampLink href="/setup">{t("start")}</StampLink>
        ) : subscribed ? (
          <>
            <p role="status" className="font-type text-case">
              {t("status", { status: subscription.data?.status ?? "active" })}
            </p>
            <ManageSubscription />
          </>
        ) : (
          <StampButton disabled={!subscription.isSuccess || redirecting} onClick={() => void checkout()}>
            {t("checkout")}
          </StampButton>
        )}
        <HandNote>{t("demo")}</HandNote>
        {error ? (
          <div role="alert" className="flex flex-col items-start gap-2">
            <p className="text-body">{errorMessage(error)}</p>
            <TypedButton onClick={() => void retry()}>{t("retry")}</TypedButton>
          </div>
        ) : null}
        {subscription.error || checkoutError ? (
          <p role="alert" className="font-type text-label text-gentle-error-fg">
            {errorMessage(subscription.error ?? checkoutError)}
          </p>
        ) : null}
      </div>
    </NotebookPage>
  );
}
