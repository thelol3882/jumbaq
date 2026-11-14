"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCheckout, type Subscription } from "@/features/billing";
import { CertificateCard, RankStamp, useStartNextCase, type Accusation, type Case, type Certificate } from "@/features/cases";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { StampButton } from "@/shared/components/notebook";
import { formatDay } from "@/shared/lib/dates";

export type AccuseViewProps = {
  current: Case;
  solved: Accusation | null;
  onSolved: (result: Accusation) => void;
  detectivesLabel: string | undefined;
  /** Loaded by the wrapper once the case is solved. */
  certificate: Certificate | undefined;
  /** Loaded by the wrapper once the case is solved: the next case button says nothing of the price to a subscriber. */
  /** Undefined while loading, null when it could not be loaded (then the price is told, as to anyone not subscribed). */
  subscription: Subscription | null | undefined;
};

export function SolvedStory({ current, solved, large = false }: { current: Case; solved: Accusation | null; large?: boolean }) {
  const t = useTranslations("widget.accuse");
  const culprit = current.suspects.find((s) => s.id === solved?.culprit_id)?.name;
  return (
    <div className="flex flex-col">
      <p className="font-type text-case">{t("closed", { number: current.number })}</p>
      <h1 className={`mt-2 font-bold ${large ? "text-[3rem] leading-[1.1]" : "text-display"}`}>
        {culprit ? t("itWas", { name: culprit }) : current.title}
      </h1>
      {solved?.reveal ? (
        <p className={`mt-3.5 max-w-[30em] font-story ${large ? "text-[1.5rem] leading-[1.55]" : "text-body"}`}>{solved.reveal}</p>
      ) : null}
      {current.rank ? (
        <div className="mt-9 ml-6">
          <RankStamp rank={current.rank} />
        </div>
      ) : null}
    </div>
  );
}

/** The certificate, the print button, and only then the next case: the win comes first. */
export function CertificateAndNext({
  current,
  certificate,
  subscription,
}: {
  current: Case;
  certificate: Certificate | undefined;
  subscription: Subscription | null | undefined;
}) {
  const t = useTranslations("widget.accuse");
  return (
    <div className="flex flex-col gap-6">
      {certificate ? (
        <>
          <CertificateCard certificate={certificate} solvedOn={formatDay(certificate.solved_at)} />
          <StampButton onClick={() => window.print()} tilt="right">
            {t("print")}
          </StampButton>
        </>
      ) : null}
      <NextCase current={current} subscription={subscription} />
    </div>
  );
}

function NextCase({ current, subscription }: { current: Case; subscription: Subscription | null | undefined }) {
  const t = useTranslations("widget.accuse");
  const router = useRouter();
  const errorMessage = useApiErrorMessage();
  const { checkout, redirecting, error: checkoutError } = useCheckout();
  // Case 2 and later need a subscription: the payment page, then back to start it.
  const { start, starting, error: startError } = useStartNextCase({ onStarted: () => router.push("/family"), onNotYet: checkout });
  const next = current.number + 1;
  const error = checkoutError ?? startError;
  // Until the subscription is known the button stays plain, so a subscriber never sees the price flash.
  const priced = subscription === null || subscription?.active === false;
  const note = priced
    ? t("next.terms")
    : subscription?.cancels_at
      ? t("next.until", { date: formatDay(subscription.cancels_at) })
      : null;
  return (
    <div className="mt-2 border-[1.5px] border-dashed border-rule-divider px-5.5 py-5">
      <p className="font-type text-label text-ink-muted">{t("next.label", { number: next })}</p>
      <button
        type="button"
        onClick={() => void start()}
        disabled={starting || redirecting}
        className="mt-1.5 inline-block border-b-2 border-ink py-1.5 text-left font-type text-[1.3125rem] font-bold disabled:opacity-60"
      >
        {t(priced ? "next.start" : "next.startPlain", { number: next })}
      </button>
      {note ? <p className="mt-1.5 font-type text-case font-normal">{note}</p> : null}
      {error ? (
        <p role="alert" className="mt-2 font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
