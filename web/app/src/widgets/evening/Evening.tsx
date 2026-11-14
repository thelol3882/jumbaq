"use client";

import { useTranslations } from "next-intl";
import { useCurrentCase, type Case } from "@/features/cases";
import { useEpisode, type Episode } from "@/features/episodes";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { HandNote, NotebookPage, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { useIsMobile } from "@/shared/hooks/useIsMobile";
import { formatOpening } from "@/shared/lib/dates";
import { EveningDesktop } from "./EveningDesktop";
import { EveningMobile } from "./EveningMobile";

/** One evening of the current case: read aloud and answer, then the result and the clue. */
export function Evening({ caseNumber, evening }: { caseNumber: number; evening: number }) {
  const t = useTranslations("widget.evening");
  const errorMessage = useApiErrorMessage();
  const isMobile = useIsMobile();
  const { current, loading: caseLoading, error: caseError, retry } = useCurrentCase();
  const slot = current?.number === caseNumber ? current.episodes.find((e) => e.number === evening) : undefined;
  const { episode, loading, writing, error } = useEpisode(slot?.id ?? null);

  const ready = current && episode?.content ? { current, episode } : null;
  if (ready) {
    const View = isMobile ? EveningMobile : EveningDesktop;
    return <View current={ready.current} episode={ready.episode as Episode & { content: NonNullable<Episode["content"]> }} />;
  }

  return (
    <NotebookPage margin>
      <Wordmark text={t("wordmark")} size="sm" />
      <div className="mt-10 flex flex-col gap-6">
        <Notice
          t={t}
          state={
            caseLoading || loading
              ? { kind: "loading" }
              : caseError || error
                ? { kind: "error", message: errorMessage(caseError ?? error) }
                : !current || !slot
                  ? { kind: "missing" }
                  : writing || slot.status === "requested" || slot.status === "generating"
                    ? { kind: "writing" }
                    : slot.available_at
                      ? { kind: "later", when: formatOpening(slot.available_at) }
                      : { kind: "missing" }
          }
          retry={() => void retry()}
          current={current}
        />
      </div>
    </NotebookPage>
  );
}

type NoticeState =
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "missing" }
  | { kind: "writing" }
  | { kind: "later"; when: string };

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
    case "writing":
      return (
        <div role="status" className="flex flex-col gap-4">
          <h1 className="text-title">{t("writing.title")}</h1>
          <HandNote>{t("writing.text")}</HandNote>
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
