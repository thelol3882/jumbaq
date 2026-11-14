"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";
import type { CaseProgress } from "@/features/cases";
import { EvidenceTag, HandNote, PlansLink, StampLink, Wordmark } from "@/shared/components/notebook";

const STEPS = ["read", "hunt", "type"] as const;
// The hand-drawn list is a little uneven on purpose.
const STEP_INDENT = ["", "ml-3.5", "ml-1"] as const;

export function Masthead() {
  const t = useTranslations("widget.landing");
  return (
    <>
      <div className="flex items-center justify-between gap-3 font-type text-label text-ink-muted">
        <span>{t("volume")}</span>
        <span>{t("edition")}</span>
        <PlansLink />
      </div>
      <h1 className="mt-4.5 self-start">
        <Wordmark text={t("wordmark")} />
      </h1>
      <HandNote className="mt-0.5 ml-33 -rotate-3 text-note-sm">{t("meaning")}</HandNote>
    </>
  );
}

export function Headline({ large = false }: { large?: boolean }) {
  const t = useTranslations("widget.landing");
  const size = large ? "max-w-xl text-[2.6rem] leading-[1.18]" : "max-w-80 text-[1.8rem] leading-[1.22]";
  return (
    <div>
      <p className={`${size} font-semibold`}>{t("headline")}</p>
      <svg aria-hidden="true" width="250" height="10" viewBox="0 0 250 10" className="mt-0.5 ml-7.5">
        <path d="M2 6 C 60 2, 150 9, 248 3" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" opacity=".7" />
      </svg>
    </div>
  );
}

export function Steps({ large = false }: { large?: boolean }) {
  const t = useTranslations("widget.landing");
  const text = large ? "text-[1.375rem] leading-[1.45]" : "text-[1.1875rem] leading-[1.4]";
  return (
    <ol className={`flex flex-col ${large ? "gap-3.5" : "gap-3"}`}>
      {STEPS.map((step, index) => (
        <li
          key={step}
          className={`grid ${large ? "grid-cols-[36px_minmax(0,1fr)]" : "grid-cols-[30px_minmax(0,1fr)]"} items-baseline ${STEP_INDENT[index]}`}
        >
          <span className={`font-type font-bold ${large ? "text-xl" : "text-lg"}`}>{index + 1}.</span>
          <span className={text}>{t(`steps.${step}`)}</span>
        </li>
      ))}
    </ol>
  );
}

export function ExampleCase() {
  const t = useTranslations("widget.landing");
  return (
    <div className="w-60 rotate-[2.5deg]">
      <EvidenceTag label={t("example.label")}>{t("example.title")}</EvidenceTag>
    </div>
  );
}

/** What the landing knows of a returning family: its names, already formatted, and where its case stands. */
export type Welcome = { names: string; count: number; progress: CaseProgress | undefined };

/** Instead of the call to action: the family this browser remembers, its case and the way back in. */
export function WelcomeCard({ welcome }: { welcome: Welcome }) {
  const t = useTranslations("widget.landing");
  const { progress } = welcome;
  return (
    <section aria-labelledby="welcome-back" className="flex flex-col gap-3 border-[1.5px] border-dashed border-rule-divider px-5.5 py-5">
      <h2 id="welcome-back" className="font-story text-body font-semibold">
        {t("welcome.title", { count: welcome.count, names: welcome.names })}
      </h2>
      {progress ? (
        <p className="font-type text-case font-normal">
          {t("welcome.progress", {
            kind: progress.kind,
            case: progress.number,
            evening: progress.kind === "evening" ? progress.evening : 0,
            total: progress.kind === "evening" ? progress.total : 0,
          })}
        </p>
      ) : null}
      <div className="mt-2">
        <StampLink href="/family">{t("welcome.continue")}</StampLink>
      </div>
    </section>
  );
}

export function Start({ href }: { href: string }) {
  const t = useTranslations("widget.landing");
  return (
    <div>
      <StampLink href={href}>{t("start")}</StampLink>
      <HandNote className="mt-2.5 ml-1.5">{t("free")}</HandNote>
    </div>
  );
}

const REVIEWER_LINES = ["login", "setup", "demo"] as const;

/** For the people who review the demo: what to expect, in the grown-up margin voice. */
export function ForReviewers() {
  const t = useTranslations("widget.landing");
  return (
    <section aria-labelledby="for-reviewers" className="mt-9 flex flex-col gap-1">
      <h2 id="for-reviewers" className="font-type text-label text-ink-muted">
        {t("reviewers.title")}
      </h2>
      <ul className="flex flex-col gap-1">
        {REVIEWER_LINES.map((line) => (
          <li key={line}>
            <HandNote>{t(`reviewers.${line}`)}</HandNote>
          </li>
        ))}
        <li>
          <HandNote>
            {t.rich("reviewers.payments", {
              plans: (chunks) => (
                <Link href="/plans" className="underline decoration-dotted decoration-2 underline-offset-4">
                  {chunks}
                </Link>
              ),
            })}
          </HandNote>
        </li>
      </ul>
    </section>
  );
}
