"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { CertificateCard, useGetCertificateQuery, useGetSolvedCasesQuery } from "@/features/cases";
import { useDetectivesLabel } from "@/features/families";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { DetectivesTag, HandNote, NotebookPage, PlansLink, StampButton, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { formatDay } from "@/shared/lib/dates";

/** The certificate of a solved case of this family, also after later cases were started. One column on every screen. */
export function CaseCertificate({ caseNumber }: { caseNumber: number }) {
  const t = useTranslations("widget.certificate");
  const errorMessage = useApiErrorMessage();
  const detectivesLabel = useDetectivesLabel();
  const solvedCases = useGetSolvedCasesQuery();
  const solved = solvedCases.data?.find((item) => item.number === caseNumber);
  const certificate = useGetCertificateQuery(solved?.id ?? "", { skip: !solved });
  const noFamily = solvedCases.isError && toApiError(solvedCases.error).code === "family.no_session";
  const error = solvedCases.error ?? certificate.error;

  return (
    <NotebookPage margin>
      <div className="flex items-center justify-between gap-4">
        <div className="flex flex-col items-start">
          <Link href="/family" aria-label={t("back")}>
            <Wordmark text={t("wordmark")} size="sm" />
          </Link>
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <PlansLink />
      </div>
      <div className="mt-10 flex flex-col gap-8">
        {certificate.data ? (
          <>
            <CertificateCard certificate={certificate.data} solvedOn={formatDay(certificate.data.solved_at)} />
            <StampButton onClick={() => window.print()} tilt="right">
              {t("print")}
            </StampButton>
            <Link href="/family" className="font-type text-label text-ink-muted underline decoration-dotted decoration-2 underline-offset-[5px]">
              {t("back")}
            </Link>
          </>
        ) : noFamily ? (
          <>
            <h1 className="text-title">{t("noFamily.title")}</h1>
            <HandNote>{t("noFamily.note")}</HandNote>
            <StampLink href="/setup">{t("noFamily.start")}</StampLink>
          </>
        ) : error ? (
          <div role="alert" className="flex flex-col items-start gap-3">
            <p className="text-body">{errorMessage(error)}</p>
            <TypedButton onClick={() => void (solvedCases.isError ? solvedCases.refetch() : certificate.refetch())}>{t("retry")}</TypedButton>
          </div>
        ) : solvedCases.isSuccess && !solved ? (
          <>
            <h1 className="text-title">{t("notFound.title")}</h1>
            <HandNote>{t("notFound.text")}</HandNote>
            <StampLink href="/family">{t("back")}</StampLink>
          </>
        ) : (
          <p role="status" className="font-type text-case font-normal text-ink-muted">
            {t("loading")}
          </p>
        )}
      </div>
    </NotebookPage>
  );
}
