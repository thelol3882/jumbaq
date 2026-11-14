"use client";

import { useFormatter, useTranslations } from "next-intl";
import { useState } from "react";
import { inOpening, tonight, WritingProgress, type Case } from "@/features/cases";
import { useOpenNowMutation } from "@/features/episodes";
import { HandNote, StampLink, TypedButton } from "@/shared/components/notebook";
import { formatOpening } from "@/shared/lib/dates";
import { Opening } from "./Opening";

/** How the page waits while the worker writes: slow after a few minutes, and a way to ask again. */
export type Waiting = { slow: boolean; onCheck: () => void };

/** The one thing to do tonight, and the stamp for it. */
export function Tonight({
  current,
  waiting,
  detectives,
  large = false,
}: {
  current: Case;
  waiting: Waiting;
  detectives: readonly string[];
  large?: boolean;
}) {
  const t = useTranslations("widget.family");
  const [openNow, opening] = useOpenNowMutation();
  // Without demo mode the server refuses; then the button goes away for good.
  const [demoRefused, setDemoRefused] = useState(false);
  const step = tonight(current, new Date());
  const base = `/cases/${current.number}`;
  const title = large ? "text-[2.875rem] leading-[1.12]" : "text-title";

  if (inOpening(current)) return <Opening current={current} detectives={detectives} waiting={waiting} large={large} />;

  switch (step.kind) {
    case "writing":
      return <Writing current={current} waiting={waiting} detectives={detectives} large={large} />;
    case "read":
      return (
        <div className="flex flex-col gap-6">
          <div>
            <p className="font-type text-case text-accent-red">
              {t("eveningOf", { number: step.evening.number, total: current.episodes.length })}
            </p>
            <h1 className={`mt-2.5 max-w-2xl ${title} font-bold`}>{current.title}</h1>
          </div>
          <div className={large ? "self-start" : ""}>
            <StampLink href={`${base}/evenings/${step.evening.number}`} fit={large}>
              {t("read")}
            </StampLink>
          </div>
          <HandNote lead={t("note.lead")} className="max-w-xl -rotate-1">
            {t("note.text")}
          </HandNote>
        </div>
      );
    case "waits":
      return (
        <div className="flex flex-col gap-4">
          <p className="font-type text-case text-accent-red">{t("doneTonight")}</p>
          <h1 className={`max-w-2xl ${title} font-bold`}>{current.title}</h1>
          <p className="text-body">
            {t("opens", { number: step.evening.number, when: formatOpening(step.opensAt) })}
          </p>
          {demoRefused || !step.evening.id ? null : (
            <TypedButton
              className="self-start"
              disabled={opening.isLoading}
              onClick={async () => {
                try {
                  await openNow(step.evening.id as string).unwrap();
                } catch {
                  setDemoRefused(true);
                }
              }}
            >
              {t("openNow")}
            </TypedButton>
          )}
        </div>
      );
    case "accuse":
      return (
        <div className="flex flex-col gap-6">
          <p className="font-type text-case text-accent-red">{t("allPlayed")}</p>
          <h1 className={`max-w-2xl ${title} font-bold`}>{t("accuseTitle")}</h1>
          <div className={large ? "self-start" : ""}>
            <StampLink href={`${base}/accuse`} fit={large}>
              {t("accuse")}
            </StampLink>
          </div>
        </div>
      );
    case "solved":
      return (
        <div className="flex flex-col gap-6">
          <p className="font-type text-case text-accent-red">{t("solved")}</p>
          <h1 className={`max-w-2xl ${title} font-bold`}>{current.title}</h1>
          <div className={large ? "self-start" : ""}>
            <StampLink href={`${base}/accuse`} fit={large}>
              {t("certificate")}
            </StampLink>
          </div>
        </div>
      );
    case "failed":
      return (
        <div className="flex flex-col gap-4">
          <p className="font-type text-case text-accent-red">{t("tonight")}</p>
          <h1 className={`${title} font-bold`}>{t("failed.title")}</h1>
          <HandNote>{t("failed.text")}</HandNote>
        </div>
      );
  }
}

/** Right after the setup, before the worker has opened case 1. */
export function TonightPending({
  waiting,
  detectives,
  large = false,
}: {
  waiting: Waiting;
  detectives: readonly string[];
  large?: boolean;
}) {
  return <Opening current={undefined} detectives={detectives} waiting={waiting} large={large} />;
}

/** A later evening is being written: the step, and what the parent can do meanwhile. */
function Writing({
  current,
  waiting,
  detectives,
  large,
}: {
  current: Case;
  waiting: Waiting;
  detectives: readonly string[];
  large: boolean;
}) {
  const t = useTranslations("widget.family");
  const format = useFormatter();
  return (
    <div role="status" className="flex flex-col gap-7">
      <div>
        <p className="font-type text-case text-accent-red">{t("tonight")}</p>
        <h1 className={`mt-2.5 max-w-2xl ${large ? "text-[2.875rem] leading-[1.12]" : "text-title"} font-bold`}>
          {current.title ?? t("writing.title")}
        </h1>
      </div>
      <WritingProgress current={current} slow={waiting.slow} onCheck={waiting.onCheck} />
      {waiting.slow ? null : (
        <HandNote lead={t("writing.meanwhileLead")} className="max-w-xl -rotate-1">
          {t("writing.meanwhile", { names: format.list(detectives) })}
        </HandNote>
      )}
    </div>
  );
}
