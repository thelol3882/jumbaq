"use client";

import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useCheckout } from "@/features/billing";
import { CertificateCard, RankStamp, useGetCertificateQuery, useStartNextCaseMutation, type Accusation, type Case } from "@/features/cases";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { StampButton } from "@/shared/components/notebook";
import { formatDay } from "@/shared/lib/dates";

export type AccuseViewProps = {
  current: Case;
  solved: Accusation | null;
  onSolved: (result: Accusation) => void;
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
export function CertificateAndNext({ current }: { current: Case }) {
  const t = useTranslations("widget.accuse");
  const certificate = useGetCertificateQuery(current.id);
  return (
    <div className="flex flex-col gap-6">
      {certificate.data ? (
        <>
          <CertificateCard certificate={certificate.data} solvedOn={formatDay(certificate.data.solved_at)} />
          <StampButton onClick={() => window.print()} tilt="right">
            {t("print")}
          </StampButton>
        </>
      ) : null}
      <NextCase current={current} />
    </div>
  );
}

function NextCase({ current }: { current: Case }) {
  const t = useTranslations("widget.accuse");
  const router = useRouter();
  const errorMessage = useApiErrorMessage();
  const [startNext, starting] = useStartNextCaseMutation();
  const { checkout, redirecting, error: checkoutError } = useCheckout();
  const next = current.number + 1;

  const start = async () => {
    try {
      await startNext().unwrap();
      router.push("/family");
    } catch (error) {
      // Case 2 and later need a subscription: the payment page, then back to start it.
      if (toApiError(error).code === "billing.payment_required") await checkout();
    }
  };

  const error = checkoutError ?? (starting.error && toApiError(starting.error).code !== "billing.payment_required" ? starting.error : undefined);
  return (
    <div className="mt-2 border-[1.5px] border-dashed border-rule-divider px-5.5 py-5">
      <p className="font-type text-label text-ink-muted">{t("next.label", { number: next })}</p>
      <button
        type="button"
        onClick={() => void start()}
        disabled={starting.isLoading || redirecting}
        className="mt-1.5 inline-block border-b-2 border-ink py-1.5 font-type text-[1.3125rem] font-bold disabled:opacity-60"
      >
        {t("next.start", { number: next })}
      </button>
      <p className="mt-1.5 font-type text-case font-normal">{t("next.terms")}</p>
      {error ? (
        <p role="alert" className="mt-2 font-type text-label text-gentle-error-fg">
          {errorMessage(error)}
        </p>
      ) : null}
    </div>
  );
}
