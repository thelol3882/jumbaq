"use client";

import { useFormatter, useTranslations } from "next-intl";
import { openingStamps, tonight, type Case } from "@/features/cases";
import { ReadAloud } from "@/features/episodes";
import { HandNote, ProgressStamps, StampLink, TypedButton } from "@/shared/components/notebook";
import { formatOpening } from "@/shared/lib/dates";
import type { Waiting } from "./Tonight";

const OATH = ["look", "search", "culprit", "end"] as const;

/**
 * The wait for evening 1 as the start of the game: the oath at once, the suspects when the case
 * is planned, evening 1 when it is written. Each part is added below the last, so nothing moves
 * while the parent reads aloud.
 */
export function Opening({
  current,
  detectives,
  waiting,
  large = false,
}: {
  current: Case | undefined;
  detectives: readonly string[];
  waiting: Waiting;
  large?: boolean;
}) {
  const t = useTranslations("widget.family");
  const format = useFormatter();
  const stamps = openingStamps(current);
  const step = current ? tonight(current, new Date()) : undefined;

  return (
    <div className="flex flex-col gap-9">
      <div className="flex flex-col gap-4">
        <p className="font-type text-case text-accent-red">{t("opening.label")}</p>
        <h1 className={`max-w-2xl ${large ? "text-display-lg" : "text-title"} font-bold`}>
          {t("opening.title")}
        </h1>
        <div role="status">
          <ProgressStamps
            doneLabel={t("opening.stamps.done")}
            notYetLabel={t("opening.stamps.notYet")}
            stamps={[
              { key: "opened", label: t("opening.stamps.opened"), done: stamps.opened },
              { key: "suspects", label: t("opening.stamps.suspects"), done: stamps.suspects },
              { key: "firstClue", label: t("opening.stamps.firstClue"), done: stamps.firstClue },
            ]}
          />
        </div>
        <HandNote lead={t("opening.note.lead")} className="max-w-xl -rotate-1">
          {t("opening.note.text")}
        </HandNote>
        <HandNote className="max-w-xl">{t("opening.saved")}</HandNote>
      </div>

      {/* The wide page has no margin rule, so the label gets its room here. */}
      <div className={`flex flex-col gap-9 ${large ? "pl-14" : ""}`}>
        <ReadAloud large={large}>
          <p>{t("opening.oath.intro", { count: detectives.length, names: format.list(detectives) })}</p>
          {OATH.map((line) => (
            <p key={line} className={line === "end" ? "font-bold" : "italic"}>
              {t(`opening.oath.${line}`, { count: detectives.length })}
            </p>
          ))}
        </ReadAloud>

        {current && stamps.suspects ? (
          <ReadAloud large={large}>
            <p>{t("opening.suspects.intro", { title: current.title ?? "", count: current.suspects.length })}</p>
            <ul className="flex flex-col gap-3">
              {current.suspects.map((s) => (
                <li key={s.id}>
                  {t.rich("opening.suspects.item", {
                    name: s.name,
                    description: s.description,
                    b: (chunks) => <b className="font-type font-bold">{chunks}</b>,
                  })}
                </li>
              ))}
            </ul>
          </ReadAloud>
        ) : null}
      </div>

      <div aria-live="polite" className="flex flex-col gap-4">
        {step?.kind === "read" && step.evening.number === 1 ? (
          <>
            <h2 className="font-type text-case font-bold text-accent-red">{t("opening.ready.title")}</h2>
            <div className={large ? "self-start" : ""}>
              <StampLink href={`/cases/${current?.number}/evenings/1`} fit={large}>
                {t("opening.ready.start")}
              </StampLink>
            </div>
          </>
        ) : step?.kind === "waits" && step.evening.number === 1 ? (
          <p className="text-body">{t("opening.ready.opens", { when: formatOpening(step.opensAt) })}</p>
        ) : waiting.slow ? (
          <div className="flex flex-col items-start gap-2">
            <HandNote lead={t("opening.slow.lead")}>{t("opening.slow.text")}</HandNote>
            <TypedButton onClick={waiting.onCheck}>{t("opening.slow.retry")}</TypedButton>
          </div>
        ) : null}
      </div>
    </div>
  );
}
