"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import { EveningBoxes, SuspectTable, type Case } from "@/features/cases";
import { ClueTag, type Episode } from "@/features/episodes";
import { StampLink, Wordmark } from "@/shared/components/notebook";

export type ShownEpisode = Episode & { content: NonNullable<Episode["content"]> };

export function EveningHeader({ current, episode, wide = false }: { current: Case; episode: ShownEpisode; wide?: boolean }) {
  const t = useTranslations("widget.evening");
  return (
    <header
      className={`flex flex-wrap items-center justify-between gap-4 ${wide ? "border-b-[1.5px] border-rule-strong pb-4.5" : ""}`}
    >
      <Link href="/family" aria-label={t("toCaseFile")}>
        <Wordmark text={t("wordmark")} size="sm" />
      </Link>
      <div className="flex items-center gap-3">
        <span className="font-type text-case">
          {t("eveningOf", { number: episode.number, total: current.episodes.length })}
        </span>
        {wide ? <EveningBoxes episodes={current.episodes} /> : null}
      </div>
    </header>
  );
}

/** After the answer: the new exhibit, the suspects as they stand, and what comes next. */
export function AfterTheAnswer({ current, episode }: { current: Case; episode: ShownEpisode }) {
  const t = useTranslations("widget.evening");
  const result = episode.content.result;
  const last = episode.number === current.episodes.length;
  return (
    <>
      {result ? <ClueTag number={episode.number} text={result.case_clue} /> : null}
      {current.suspects.length ? (
        <section aria-labelledby="evening-suspects">
          <h2 id="evening-suspects" className="mb-2.5 font-type text-label font-normal text-ink-muted">
            {t("suspects")}
          </h2>
          <SuspectTable suspects={current.suspects} clues={current.clues} />
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
