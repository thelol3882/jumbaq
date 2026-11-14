"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { useCurrentCase, WritingProgress, type Case } from "@/features/cases";
import { useEpisode, type Episode } from "@/features/episodes";
import { useDetectivesLabel, useFamily } from "@/features/families";
import { toApiError } from "@/shared/api/errors";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { DetectivesTag, HandNote, NotebookPage, PlansLink, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { useRefetchAt } from "@/shared/hooks/useRefetchAt";
import { formatOpening } from "@/shared/lib/dates";
import { EveningDesktop } from "./EveningDesktop";
import { EveningMobile } from "./EveningMobile";
import type { ShownEpisode } from "./parts";
import { codeBreaker } from "./services/codeBreaker";

function hasContent(episode: Episode | undefined): episode is ShownEpisode {
  return episode?.content != null;
}

/** One evening of the current case: the riddle, the code, the suspect to cross out, then the result. */
export function Evening({ caseNumber, evening }: { caseNumber: number; evening: number }) {
  const t = useTranslations("widget.evening");
  const errorMessage = useApiErrorMessage();
  const isMobile = useIsMobile();
  const { current, loading: caseLoading, error: caseError, slow: caseSlow, retry } = useCurrentCase();
  const slot = current?.number === caseNumber ? current.episodes.find((e) => e.number === evening) : undefined;
  const { episode, loading, writing, slow, error, retry: retryEpisode } = useEpisode(slot?.id ?? null);
  const { family } = useFamily();
  const detectivesLabel = useDetectivesLabel();

  const recheck = () => {
    void retry();
    if (slot?.id) void retryEpisode();
  };

  const state: NoticeState =
    caseLoading || loading
      ? { kind: "loading" }
      : caseError && toApiError(caseError).code === "family.no_session"
        ? { kind: "noFamily" }
        : caseError || error
          ? { kind: "error", message: errorMessage(caseError ?? error) }
          : !current || !slot
            ? { kind: "missing" }
            : slot.status === "failed" || episode?.status === "failed"
              ? { kind: "failed" }
              : writing || slot.status === "requested" || slot.status === "generating"
                ? { kind: "writing", slow: slow || caseSlow }
                : slot.available_at
                  ? { kind: "later", when: formatOpening(slot.available_at), at: slot.available_at }
                  : { kind: "missing" };
  useRefetchAt(state.kind === "later" ? state.at : null, recheck);

  if (current && hasContent(episode)) {
    const View = isMobile ? EveningMobile : EveningDesktop;
    return (
      <View
        current={current}
        episode={episode}
        codeBreaker={codeBreaker(family?.kids ?? [])}
        detectivesLabel={detectivesLabel}
        demoMode={family?.demo_mode ?? false}
      />
    );
  }

  return (
    <NotebookPage margin>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-col items-start">
          <Link href="/family" aria-label={t("toCaseFile")}>
            <Wordmark text={t("wordmark")} size="sm" />
          </Link>
          {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
        </div>
        <div className="flex items-center gap-4">
          {current && slot ? (
            <span className="font-type text-case">{t("eveningOf", { number: evening, total: current.episodes.length })}</span>
          ) : null}
          <PlansLink />
        </div>
      </div>
      <div className="mt-10 flex flex-col gap-6">
        <Notice t={t} state={state} retry={recheck} current={current} />
      </div>
    </NotebookPage>
  );
}

type NoticeState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "missing" }
  | { kind: "noFamily" }
  | { kind: "failed" }
  | { kind: "writing"; slow: boolean }
  | { kind: "later"; when: string; at: string };

function Notice({
  t,
  state,
  retry,
  current,
}: {
  t: ReturnType<typeof useTranslations<"widget.evening">>;
  state: NoticeState;
  retry: () => void;
  current: Case | undefined;
}) {
  switch (state.kind) {
    case "loading":
      return (
        <p role="status" className="font-type text-case font-normal text-ink-muted">
          {t("loading")}
        </p>
      );
    case "error":
      return (
        <div role="alert" className="flex flex-col items-start gap-3">
          <p className="text-body">{state.message}</p>
          <TypedButton onClick={retry}>{t("retry")}</TypedButton>
        </div>
      );
    case "noFamily":
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">{t("noFamily.title")}</h1>
          <HandNote>{t("noFamily.note")}</HandNote>
          <StampLink href="/setup">{t("noFamily.start")}</StampLink>
        </div>
      );
    case "failed":
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">{t("failed.title")}</h1>
          <HandNote>{t("failed.text")}</HandNote>
          <StampLink href="/family">{t("back")}</StampLink>
        </div>
      );
    case "writing":
      return (
        <div role="status" className="flex flex-col gap-7">
          <div>
            {current?.title ? <p className="font-type text-case text-accent-red">{current.title}</p> : null}
            <h1 className="mt-2.5 text-title">{t("writing.title")}</h1>
          </div>
          <WritingProgress current={current} slow={state.slow} onCheck={retry} />
        </div>
      );
    case "later":
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">{t("later.title")}</h1>
          <p className="text-body">{t("later.text", { when: state.when })}</p>
          <StampLink href="/family">{t("back")}</StampLink>
        </div>
      );
    case "missing":
      return (
        <div className="flex flex-col gap-6">
          <h1 className="text-title">{t("missing.title")}</h1>
          <HandNote>{current ? t("missing.text") : t("missing.noCase")}</HandNote>
          <StampLink href="/family">{t("back")}</StampLink>
        </div>
      );
  }
}
