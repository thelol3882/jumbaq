"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { EveningBoxes, SuspectTable, type Case } from "@/features/cases";
import { ClueTag, DecodeStep, StrikeStep, useSkipEvening, type Episode } from "@/features/episodes";
import { useApiErrorMessage } from "@/shared/api/useApiErrorMessage";
import { DemoControls, DetectivesTag, HandNote, PlansLink, StampLink, TypedButton, Wordmark } from "@/shared/components/notebook";
import { withTonightsClue } from "./services/tonightsClues";

export type ShownEpisode = Episode & { content: NonNullable<Episode["content"]> };

export function EveningHeader({
  current,
  episode,
  detectivesLabel,
  wide = false,
}: {
  current: Case;
  episode: ShownEpisode;
  detectivesLabel: string | undefined;
  wide?: boolean;
}) {
  const t = useTranslations("widget.evening");
  return (
    <header
      className={`flex flex-wrap items-center justify-between gap-x-4 gap-y-2 ${wide ? "border-b-[1.5px] border-rule-strong pb-4.5" : ""}`}
    >
      <div className="flex flex-col items-start">
        <Link href="/family" aria-label={t("toCaseFile")}>
          <Wordmark text={t("wordmark")} size="sm" />
        </Link>
        {detectivesLabel ? <DetectivesTag text={detectivesLabel} /> : null}
      </div>
      {/* On a phone the evening takes its own row, so Plans stays at the right edge. */}
      <div className="contents sm:flex sm:items-center sm:gap-3">
        <span className="order-last basis-full font-type text-case sm:order-none sm:basis-auto">
          {t("eveningOf", { number: episode.number, total: current.episodes.length })}
        </span>
        {wide ? <EveningBoxes episodes={current.episodes} /> : null}
        <PlansLink />
      </div>
    </header>
  );
}

/** After the answer: the new exhibit, the suspects as they stand, and what comes next. */
export function AfterTheAnswer({ current, episode }: { current: Case; episode: ShownEpisode }) {
  const t = useTranslations("widget.evening");
  const result = episode.content.result;
  const last = episode.number === current.episodes.length;
  const aboutName = result?.revealed_suspect
    ? current.suspects.find((s) => s.id === result.struck_suspect_id)?.name
    : undefined;
  return (
    <>
      {result ? <ClueTag number={episode.number} text={result.case_clue} /> : null}
      {aboutName ? <HandNote>{t("revealedSuspect", { name: aboutName })}</HandNote> : null}
      {current.suspects.length ? (
        <section aria-labelledby="evening-suspects">
          <h2 id="evening-suspects" className="mb-2.5 font-type text-label font-normal text-ink-muted">
            {t("suspects")}
          </h2>
          <SuspectTable suspects={current.suspects} clues={withTonightsClue(current.clues, episode.number, result)} />
        </section>
      ) : null}
      {last ? (
        <StampLink href={`/cases/${current.number}/accuse`}>{t("toAccuse")}</StampLink>
      ) : (
        <StampLink href="/family">{t("doneTonight")}</StampLink>
      )}
    </>
  );
}

/** The steps after the riddle, in the main column: decode the clue, then strike out a suspect. Nothing for the other steps. */
export function StepMain({
  current,
  episode,
  codeBreaker,
  inlineKey = false,
  large = false,
}: {
  current: Case;
  episode: ShownEpisode;
  codeBreaker?: string;
  inlineKey?: boolean;
  large?: boolean;
}) {
  const { step, decode, strike, answered } = episode.content;
  if (step === "decode" && decode && answered) {
    return (
      <DecodeStep
        episodeId={episode.id}
        decode={decode}
        resolution={answered.resolution}
        codeBreaker={codeBreaker}
        inlineKey={inlineKey}
        large={large}
      />
    );
  }
  if (step === "strike" && strike) {
    return (
      <StrikeStep episodeId={episode.id} number={episode.number} strike={strike} suspects={current.suspects} large={large} />
    );
  }
  return null;
}

/** For reviewers: plays the evening out from the answer, decode or strike step. */
export function EveningDemo({ episode, demoMode }: { episode: ShownEpisode; demoMode: boolean }) {
  const t = useTranslations("widget.evening");
  const errorMessage = useApiErrorMessage();
  const skipper = useSkipEvening();
  if (!demoMode || skipper.refused || episode.content.step === "done") return null;
  return (
    <DemoControls title={t("demo.title")} note={t("demo.note")}>
      <TypedButton disabled={skipper.skipping} onClick={() => void skipper.skip(episode.id)}>
        {t("demo.skip")}
      </TypedButton>
      {skipper.error ? (
        <p role="alert" className="font-type text-label text-gentle-error-fg">
          {errorMessage(skipper.error)}
        </p>
      ) : null}
    </DemoControls>
  );
}
