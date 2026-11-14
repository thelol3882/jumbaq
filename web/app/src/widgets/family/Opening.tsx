"use client";

import { useFormatter, useTranslations } from "next-intl";
import type { ReactNode } from "react";
import { openingStamps, tonight, type Case } from "@/features/cases";
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
  const aloud = large ? "text-[1.625rem] leading-[1.6]" : "text-aloud";

  return (
    <div className="flex flex-col gap-9">
      <div className="flex flex-col gap-4">
        <p className="font-type text-case text-accent-red">{t("opening.label")}</p>
        <h1 className={`max-w-2xl ${large ? "text-[2.875rem] leading-[1.12]" : "text-title"} font-bold`}>
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
      </div>

      <ReadAloud label={t("opening.readAloud")}>
        <p className={`font-story ${aloud} text-aloud-fg`}>
          {t("opening.oath.intro", { count: detectives.length, names: format.list(detectives) })}
        </p>
        {OATH.map((line) => (
          <p key={line} className={`font-story ${aloud} text-aloud-fg ${line === "end" ? "font-bold" : "italic"}`}>
            {t(`opening.oath.${line}`, { count: detectives.length })}
          </p>
        ))}
      </ReadAloud>

      {current && stamps.suspects ? (
        <ReadAloud label={t("opening.readAloud")}>
          <p className={`font-story ${aloud} text-aloud-fg`}>
            {t("opening.suspects.intro", { title: current.title ?? "", count: current.suspects.length })}
          </p>
          <ul className="flex flex-col gap-3">
            {current.suspects.map((s) => (
              <li key={s.id} className={`font-story ${aloud} text-aloud-fg`}>
                <b className="font-type font-bold">{s.name}</b>: {s.description}
              </li>
            ))}
          </ul>
        </ReadAloud>
      ) : null}

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

/** Text the parent reads to the kids, with the red label the brand gives read-aloud text. */
function ReadAloud({ label, children }: { label: string; children: ReactNode }) {
  return (
    <section className="flex max-w-[34em] flex-col gap-3">
      <p className="font-type text-label-sm text-aloud-label">{label}</p>
      {children}
    </section>
  );
}
